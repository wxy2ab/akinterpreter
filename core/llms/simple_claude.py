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
from tenacity import retry, retry_if_exception,wait_fixed,stop_after_attempt

class SimpleClaudeAwsClient(LLMApiClient):
    def __init__(self, 
                aws_access_key_id: Optional[str] = None,
                aws_secret_access_key: Optional[str] = None,
                aws_session_token: Optional[str] = None,
                aws_region: str = "us-west-2", 
                model: str = "anthropic.claude-3-5-sonnet-20241022-v2:0",
                temperature: float = 0.5,
                top_p: float = 1.0,
                top_k: int = 250,
                max_tokens: int = 4096,
                stop_sequences: Optional[List[str]] = None,
                anthropic_version: str = "2023-06-01"):
        self.aws_region = aws_region
        self.model = model
        self.temperature = temperature
        self.top_p = top_p
        self.top_k = top_k
        self.max_tokens = max_tokens
        self.stop_sequences = stop_sequences or []
        self.anthropic_version = anthropic_version
        self.client = self._create_client(aws_access_key_id, aws_secret_access_key, aws_session_token)
        self.history = []
        self.stat = {
            "call_count": {"text_chat": 0, "image_chat": 0, "tool_chat": 0},
            'input_tokens': 0,
            'output_tokens': 0,
            "total_tokens": 0
        }

    def _create_client(self, aws_access_key_id, aws_secret_access_key, aws_session_token):
        config = Config()
        credentials = self._get_aws_credentials(aws_access_key_id, aws_secret_access_key, aws_session_token, config)
        return AnthropicBedrock(**credentials, aws_region=self.aws_region)

    def _get_aws_credentials(self, aws_access_key_id, aws_secret_access_key, aws_session_token, config):
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

    def _update_stats(self, response):
        if hasattr(response, 'usage'):
            self.stat['input_tokens'] += response.usage.input_tokens
            self.stat['output_tokens'] += response.usage.output_tokens
            self.stat["total_tokens"] += response.usage.input_tokens + response.usage.output_tokens

    @handle_max_tokens
    def text_chat(self, message: str, max_tokens: Optional[int] = None, is_stream: bool = False) -> Union[str, Iterator[str]]:
        copy_history= self.history.copy()
        copy_history.append({"role": "user", "content": message})
        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens or self.max_tokens,
            messages=copy_history,
            stream=is_stream,
            temperature=self.temperature,
            top_p=self.top_p,
            top_k=self.top_k,
            stop_sequences=self.stop_sequences
        )
        self._update_stats(response)
        self.stat["call_count"]["text_chat"] += 1
        if is_stream:
            return self._handle_stream_response(response,message)
        else:
            assistant_message = response.content[0].text
            self.history.append({"role": "user", "content": message})
            self.history.append({"role": "assistant", "content": assistant_message})
            return assistant_message

    def _handle_stream_response(self, response,message=None):
        full_response = ""
        for chunk in response:
            if chunk.type == 'content_block':
                if chunk.content_block.type == 'text':
                    text = chunk.content_block.text
                    full_response += text
                    yield text
            elif chunk.type == 'content_block_delta':
                if chunk.delta.type == 'text_delta':
                    text =  chunk.delta.text
                    full_response += text
                    yield text
        self.history.append({"role": "user", "content": message})
        self.history.append({"role": "assistant", "content": full_response})

    def tool_chat(self, user_message: str, tools: List[Dict[str, Any]], function_module: Any, max_tokens: Optional[int]  = None, is_stream: bool = False) -> Union[str, Iterator[str]]:
        self.history.append({"role": "user", "content": user_message})
        cleaned_tools = [tool.copy() for tool in tools]
        for tool in cleaned_tools:
            tool.pop('output_schema', None)

        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens or self.max_tokens,
            messages=self.history,
            tools=cleaned_tools,
            stream=is_stream,
            temperature=self.temperature,
            top_p=self.top_p,
            top_k=self.top_k,
            stop_sequences=self.stop_sequences
        )

        self._update_stats(response)
        self.stat["call_count"]["tool_chat"] += 1

        if is_stream:
            return self._handle_tool_stream(response, function_module, max_tokens)
        else:
            return self._handle_tool_response(response, function_module, max_tokens)

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

    @retry(retry=retry_if_exception(Exception),wait=wait_fixed(5),stop=stop_after_attempt(3) )
    def one_chat(self, message: Union[str, List[Union[str, Any]]], max_tokens: Optional[ int ]= None, is_stream: bool = False) -> Union[str, Iterator[str]]:
        messages = [{"role": "user", "content": message}] if isinstance(message, str) else message
        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens or self.max_tokens,
            messages=messages,
            stream=is_stream,
            temperature=self.temperature,
            top_p=self.top_p,
            top_k=self.top_k,
            stop_sequences=self.stop_sequences
        )
        self._update_stats(response)
        self.stat["call_count"]["text_chat"] += 1
        if is_stream:
            return self._handle_stream_response(response)
        else:
            return response.content[0].text

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

    def get_stats(self) -> Dict[str, Any]:
        return self.stat

    def audio_chat(self, message: str, audio_path: str) -> str:
        raise NotImplementedError("Audio chat is not supported in this version of Claude API client.")

    def video_chat(self, message: str, video_path: str) -> str:
        raise NotImplementedError("Video chat is not supported in this version of Claude API client.")
    
    @property
    def stop(self):
        return self._stop_sequences

    @stop.setter
    def stop(self, value):
        self._stop_sequences = value
    