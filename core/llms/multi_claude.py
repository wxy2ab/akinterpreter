from datetime import datetime
import inspect
from typing import List, Dict, Any, Optional, Union, Iterator
from anthropic import AnthropicBedrock
import boto3
import json
import os
import base64
from PIL import Image
import io
from ._llm_api_client import LLMApiClient
from ..utils.config_setting import Config
from ..utils.handle_max_tokens import handle_max_tokens
from tenacity import retry, wait_fixed, retry_if_exception, stop_after_attempt
import random
from collections import defaultdict
import threading
import time

class RegionClientPool:
    def __init__(self, regions: List[str], credentials: Dict[str, Any]):
        self.regions = regions
        self.credentials = credentials
        self.clients: Dict[str, AnthropicBedrock] = {}
        self.request_counts = defaultdict(int)
        self.rate_limits = {region: {"tpm": 0, "rpm": 0, "last_reset": time.time()} for region in regions}
        self.lock = threading.Lock()
        self._initialize_clients()

    def _initialize_clients(self):
        """初始化所有区域的客户端"""
        for region in self.regions:
            self.clients[region] = AnthropicBedrock(
                aws_access_key=self.credentials.get("aws_access_key"),
                aws_secret_key=self.credentials.get("aws_secret_key"),
                aws_session_token=self.credentials.get("aws_session_token"),
                aws_region=region
            )

    def _reset_counters(self, region: str):
        """重置区域的计数器"""
        current_time = time.time()
        with self.lock:
            if current_time - self.rate_limits[region]["last_reset"] >= 60:
                self.rate_limits[region]["tpm"] = 0
                self.rate_limits[region]["rpm"] = 0
                self.rate_limits[region]["last_reset"] = current_time

    def _can_use_region(self, region: str) -> bool:
        """检查区域是否可用"""
        self._reset_counters(region)
        return (self.rate_limits[region]["tpm"] < 5 and  # 假设每分钟token限制
                self.rate_limits[region]["rpm"] < 50)    # 假设每分钟请求限制

    def get_available_client(self) -> tuple[AnthropicBedrock, str]:
        """获取可用的客户端和对应的区域"""
        available_regions = [r for r in self.regions if self._can_use_region(r)]
        if not available_regions:
            # 如果所有区域都达到限制，选择计数最小的
            region = min(self.regions, key=lambda r: self.request_counts[r])
        else:
            # 根据使用频率加权随机选择区域
            weights = [1.0 / (self.request_counts[r] + 1) for r in available_regions]
            region = random.choices(available_regions, weights=weights, k=1)[0]
        
        with self.lock:
            self.request_counts[region] += 1
            self.rate_limits[region]["rpm"] += 1
            
        return self.clients[region], region

    def update_token_count(self, region: str, token_count: int):
        """更新区域的token使用计数"""
        with self.lock:
            self.rate_limits[region]["tpm"] += token_count

class MultiRegionClaudeClient(LLMApiClient):
    def __init__(self, 
                regions: List[str] = None,
                aws_access_key_id: Optional[str] = None,
                aws_secret_access_key: Optional[str] = None,
                aws_session_token: Optional[str] = None,
                model: str = "anthropic.claude-3-5-sonnet-20240620-v1:0",
                temperature: float = 0.5,
                top_p: float = 1.0,
                top_k: int = 250,
                max_tokens: int = 4096,
                stop_sequences: Optional[List[str]] = None,
                anthropic_version: str = "2023-06-01"):
        
        self.regions = regions or ["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1"]
        self.model = model
        self.temperature = temperature
        self.top_p = top_p
        self.top_k = top_k
        self.max_tokens = max_tokens
        self.stop_sequences = stop_sequences or []
        self.anthropic_version = anthropic_version
        
        credentials = self._get_aws_credentials(aws_access_key_id, aws_secret_access_key, aws_session_token)
        self.client_pool = RegionClientPool(self.regions, credentials)
        
        self.history = []
        self.stat = defaultdict(lambda: {"text_chat": 0, "image_chat": 0, "tool_chat": 0})
        self.system_message = f"你是一个智能助手,擅长把复杂问题清晰明白通俗易懂地解答出来.现在的时间是：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    def _get_aws_credentials(self, aws_access_key_id, aws_secret_access_key, aws_session_token):
        config = Config()
        if config.has_key("aws_access_key_id") and config.has_key("aws_secret_access_key"):
            return {
                "aws_access_key": config.get("aws_access_key_id"),
                "aws_secret_key": config.get("aws_secret_access_key"),
                "aws_session_token": None
            }
        if aws_access_key_id and aws_secret_access_key:
            return {
                "aws_access_key": aws_access_key_id,
                "aws_secret_key": aws_secret_access_key,
                "aws_session_token": aws_session_token
            }
        return self._get_credentials_from_environment()

    def _get_credentials_from_environment(self):
        access_key = os.environ.get('AWS_ACCESS_KEY_ID')
        secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
        session_token = os.environ.get('AWS_SESSION_TOKEN')
        if access_key and secret_key:
            return {
                "aws_access_key": access_key,
                "aws_secret_key": secret_key,
                "aws_session_token": session_token
            }
        session = boto3.Session()
        credentials = session.get_credentials()
        if credentials:
            return {
                "aws_access_key": credentials.access_key,
                "aws_secret_key": credentials.secret_key,
                "aws_session_token": credentials.token
            }
        raise ValueError("AWS credentials not found. Please provide credentials or configure your environment.")

    def _update_stats(self, response, region: str):
        if hasattr(response, 'usage'):
            self.stat[region]['input_tokens'] = self.stat[region].get('input_tokens', 0) + response.usage.input_tokens
            self.stat[region]['output_tokens'] = self.stat[region].get('output_tokens', 0) + response.usage.output_tokens
            self.stat[region]["total_tokens"] = self.stat[region].get('total_tokens', 0) + response.usage.input_tokens + response.usage.output_tokens
            # 更新令牌使用计数
            self.client_pool.update_token_count(region, response.usage.input_tokens + response.usage.output_tokens)

    @handle_max_tokens
    def text_chat(self, message: str, max_tokens: Optional[int] = None, is_stream: bool = False) -> Union[str, Iterator[str]]:
        client, region = self.client_pool.get_available_client()
        copy_history = self.history.copy()
        copy_history.append({"role": "user", "content": message})
        
        response = client.messages.create(
            model=self.model,
            max_tokens=max_tokens or self.max_tokens,
            messages=copy_history,
            stream=is_stream,
            temperature=self.temperature,
            top_p=self.top_p,
            top_k=self.top_k,
            stop_sequences=self.stop_sequences,
            system=self.system_message
        )
        
        self._update_stats(response, region)
        self.stat[region]["text_chat"] += 1
        
        if is_stream:
            return self._handle_stream_response(response, message)
        else:
            assistant_message = response.content[0].text
            self.history.append({"role": "user", "content": message})
            self.history.append({"role": "assistant", "content": assistant_message})
            return assistant_message

    @retry(retry=retry_if_exception(Exception),wait=wait_fixed(5),stop=stop_after_attempt(3) )
    def one_chat(self, message: Union[str, List[Union[str, Any]]], max_tokens: Optional[int] = None, is_stream: bool = False) -> Union[str, Iterator[str]]:
        client, region = self.client_pool.get_available_client()
        messages = [{"role": "user", "content": message}] if isinstance(message, str) else message
        
        response = client.messages.create(
            model=self.model,
            max_tokens=max_tokens or self.max_tokens,
            messages=messages,
            stream=is_stream,
            temperature=self.temperature,
            top_p=self.top_p,
            top_k=self.top_k,
            stop_sequences=self.stop_sequences,
            system=self.system_message
        )

        self._update_stats(response, region)
        self.stat[region]["text_chat"] += 1
        
        if is_stream:
            return self._handle_stream_response(response)
        else:
            return response.content[0].text

    def _handle_stream_response(self, response, message=None):
        full_response = ""
        for chunk in response:
            if chunk.type == 'content_block':
                if chunk.content_block.type == 'text':
                    text = chunk.content_block.text
                    full_response += text
                    yield text
            elif chunk.type == 'content_block_delta':
                if chunk.delta.type == 'text_delta':
                    text = chunk.delta.text
                    full_response += text
                    yield text
        
        if message:
            self.history.append({"role": "user", "content": message})
            self.history.append({"role": "assistant", "content": full_response})

    def tool_chat(self, user_message: str, tools: List[Dict[str, Any]], function_module: Any, max_tokens: Optional[int] = None, is_stream: bool = False) -> Union[str, Iterator[str]]:
        client, region = self.client_pool.get_available_client()
        self.history.append({"role": "user", "content": user_message})
        
        cleaned_tools = [tool.copy() for tool in tools]
        for tool in cleaned_tools:
            tool.pop('output_schema', None)

        response = client.messages.create(
            model=self.model,
            max_tokens=max_tokens or self.max_tokens,
            messages=self.history,
            tools=cleaned_tools,
            stream=is_stream,
            temperature=self.temperature,
            top_p=self.top_p,
            top_k=self.top_k,
            stop_sequences=self.stop_sequences,
            system=self.system_message
        )

        self._update_stats(response, region)
        self.stat[region]["tool_chat"] += 1

        if is_stream:
            return self._handle_tool_stream(response, function_module, max_tokens)
        else:
            return self._handle_tool_response(response, function_module, max_tokens)

    def tool_invoke(self, messages: List[Dict[str, str]], tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        client, region = self.client_pool.get_available_client()
        cleaned_tools = [tool.copy() for tool in tools]
        for tool in cleaned_tools:
            tool.pop("output_schema", None)

        response = client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=messages,
            tools=cleaned_tools,
            stream=False,
            temperature=self.temperature,
            top_p=self.top_p,
            top_k=self.top_k,
            stop_sequences=self.stop_sequences,
            system=self.system_message
        )
        self._update_stats(response, region)
        self.stat[region]["tool_chat"] += 1
        content_parts = []
        tool_calls = []
        for block in response.content:
            if getattr(block, "type", "") == "text":
                content_parts.append(block.text)
            elif getattr(block, "type", "") == "tool_use":
                tool_calls.append({
                    "id": getattr(block, "id", ""),
                    "name": getattr(block, "name", ""),
                    "input": getattr(block, "input", {})
                })
        return self._normalize_tool_invoke_response("".join(content_parts), tool_calls)

    def _handle_tool_stream(self, response, function_module, max_tokens):
        assistant_message = ""
        current_tool_call = None
        tool_calls = []

        try:
            while True:
                event = next(response)
                
                if event.type == 'content_block_start':
                    if hasattr(event.content_block, 'type') and event.content_block.type == 'tool_use':
                        current_tool_call = {
                            "name": event.content_block.name,
                            "arguments": ""  # Initialize as empty string
                        }
                
                elif event.type == 'content_block_delta':
                    if event.delta.type == 'text_delta':
                        assistant_message += event.delta.text
                        yield event.delta.text
                    elif event.delta.type == 'input_json_delta':
                        if current_tool_call is not None and hasattr(event.delta, 'partial_json'):
                            current_tool_call["arguments"] += event.delta.partial_json
                
                elif event.type == 'content_block_stop':
                    if current_tool_call:
                        tool_calls.append(current_tool_call)
                        current_tool_call = None
                
                elif event.type == 'message_delta':
                    if hasattr(event.delta, 'stop_reason') and event.delta.stop_reason == 'tool_use':
                        break
                
                elif event.type == 'message_stop':
                    break

        except StopIteration:
            pass

        if tool_calls:
            for tool_call in tool_calls:
                function_name = tool_call["name"]
                function_args = self._parse_function_args(tool_call["arguments"], function_name, function_module)
                
                tool_result = self._execute_function(function_name, function_args, function_module)
                yield f"\n使用工具: {function_name}\n参数: {function_args}\n工具结果: {tool_result}\n"

            final_response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens or self.max_tokens,
                messages=self.history + [{"role": "assistant", "content": assistant_message},
                                         {"role": "user", "content": f"工具函数返回结果: {tool_result}"}],
                stream=True
            )

            try:
                while True:
                    chunk = next(final_response)
                    if chunk.type == 'content_block_delta' and chunk.delta.type == 'text_delta':
                        yield chunk.delta.text
            except StopIteration:
                pass

        self.history.append({"role": "assistant", "content": assistant_message})

    def _parse_function_args(self, args_str: str, function_name: str, function_module: Any) -> Dict[str, Any]:
        if not args_str.strip():
            return {}
        
        try:
            args = json.loads(args_str)
            if isinstance(args, dict):
                return args
            else:
                return {"raw_input": args}
        except json.JSONDecodeError:
            return {"raw_input": args_str}

    def _execute_function(self, function_name: str, function_args: Dict[str, Any], function_module: Any) -> Any:
        if hasattr(function_module, function_name):
            function = getattr(function_module, function_name)
            try:
                sig = inspect.signature(function)
                if len(sig.parameters) == 0:
                    return function()
                elif len(sig.parameters) == 1 and "raw_input" in function_args:
                    return function(function_args["raw_input"])
                else:
                    return function(**function_args)
            except Exception as e:
                return f"Error executing {function_name}: {str(e)}"
        else:
            return f"Function {function_name} not found in the provided module."

    def _handle_tool_response(self, response, function_module, max_tokens):
        assistant_message = ""
        tool_calls = []

        for content in response.content:
            if content.type == 'text':
                assistant_message += content.text
            elif content.type == 'tool_calls':
                tool_calls.extend(content.tool_calls)

        self.history.append({"role": "assistant", "content": assistant_message})

        if tool_calls:
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                try:
                    function_args = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    function_args = {}
                tool_result = self._execute_function(function_name, function_args, function_module)
                self.history.append({"role": "user", "content": f"工具函数返回结果{function_name}: {tool_result}"})

            final_response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=self.history
            )
            final_assistant_message = "".join([content.text for content in final_response.content if content.type == 'text'])
            self.history.append({"role": "assistant", "content": final_assistant_message})
            return f"*首轮消息：*{assistant_message}\n*使用工具：*{[tool_call.function.name for tool_call in tool_calls]}\n*最终结果：*{final_assistant_message}"
        else:
            return assistant_message

    def get_stats(self) -> Dict[str, Dict[str, Any]]:
        """获取所有区域的统计数据"""
        return dict(self.stat)

    def get_region_stats(self, region: str) -> Dict[str, Any]:
        """获取特定区域的统计数据"""
        return dict(self.stat[region])

    def image_chat(self, message: str, image_path: str, max_tokens:Optional[int] = None) -> str:
        with Image.open(image_path) as img:
            buffered = io.BytesIO()
            img.save(buffered, format=img.format)
            base64_image = base64.b64encode(buffered.getvalue()).decode('utf-8')

        image_message = {
            "role": "user", 
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": f"image/{img.format.lower()}", "data": base64_image}},
                {"type": "text", "text": message}
            ]
        }
        self.history.append(image_message)

        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens or self.max_tokens,
            messages=self.history
        )

        assistant_message = response.content[0].text
        self.history.append({"role": "assistant", "content": assistant_message})
        self._update_stats(response)
        self.stat["call_count"]["image_chat"] += 1
        return assistant_message

    def clear_chat(self) -> None:
        self.history.clear()

    @property
    def stop(self):
        return self.stop_sequences

    @stop.setter
    def stop(self, value):
        self.stop_sequences = value
