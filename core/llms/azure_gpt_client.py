import ast
import contextlib
from typing import Iterator, List, Dict, Any, Optional, Union
from openai import AzureOpenAI
import os
import base64
from PIL import Image
import io
import json
from ._llm_api_client import LLMApiClient
from ..utils.handle_max_tokens import handle_max_tokens

class AzureGPT4oClient(LLMApiClient):
    def __init__(self, 
                 api_key: Optional[str] = None,
                 azure_endpoint: Optional[str] = None,
                 max_tokens: int = 4000,
                 deployment_name: str = "gpt-4o",
                 api_version: str = "2023-05-15",
                 temperature: float = 0.7,
                 top_p: float = 1.0,
                 frequency_penalty: float = 0,
                 presence_penalty: float = 0,
                 stop: Optional[Union[str, List[str]]] = None):
        from ..utils.config_setting import Config
        config  =   Config()

        self.api_key = api_key or config.get("AZURE_OPENAI_API_KEY")
        self.azure_endpoint = azure_endpoint or config.get("AZURE_OPENAI_ENDPOINT")
        self.deployment_name = deployment_name
        self.api_version = api_version
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.top_p = top_p
        self.frequency_penalty = frequency_penalty
        self.presence_penalty = presence_penalty
        self.stop = stop
        self.client = self._create_client()
        self.history: List[dict] = []
        self.stat: Dict[str, Any] = {
            "call_count": {"text_chat": 0, "image_chat": 0, "tool_chat": 0},
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_cost": 0
        }
        self.supported_sizes = [
            (1024, 1024), (1024, 768), (768, 1024), (1024, 576), (576, 1024)
        ]

    def _create_client(self):
        if not self.api_key or not self.azure_endpoint:
            raise ValueError("Azure OpenAI API key and endpoint are required.")
        return AzureOpenAI(
            api_key=self.api_key,
            api_version=self.api_version,
            azure_endpoint=self.azure_endpoint
        )

    def _update_usage_stats(self, response):
        if hasattr(response, 'usage'):
            usage = response.usage
            self.stat["total_input_tokens"] += usage.prompt_tokens
            self.stat["total_output_tokens"] += usage.completion_tokens
            # Cost calculation would depend on your specific Azure pricing

    def _handle_streaming_response(self, response,message=None) -> Iterator[str]:
        full_response = ""
        for chunk in response:
            text = chunk.choices[0].delta.content if  chunk.choices[0].delta.content else ''
            full_response += text
            yield text
        if message:
            self.history.append({"role": "user", "content": message})
            self.history.append({"role": "assistant", "content": full_response})
    @handle_max_tokens
    def text_chat(self, message: str, is_stream: bool = False) -> Union[str, Iterator[str]]:
        copy_history= self.history.copy()
        copy_history.append({"role": "user", "content": message})
        response = self.client.chat.completions.create(
            model=self.deployment_name,
            messages=copy_history,
            max_tokens=self.max_tokens,
            stream=is_stream,
            temperature=self.temperature,
            top_p=self.top_p,
            frequency_penalty=self.frequency_penalty,
            presence_penalty=self.presence_penalty,
            stop=self.stop
        )
        self._update_usage_stats(response)
        if is_stream:
            return self._handle_streaming_response(response,message)
        else:
            self.history.append({"role": "user", "content": message})
            text_response = response['choices'][0]['text']
            self.history.append({"role": "assistant", "content": text_response})
            return text_response

    def one_chat(self, message: Union[str, List[Union[str, Any]]], is_stream: bool = False) -> Union[str, Iterator[str]]:
        response = self.client.chat.completions.create(
            model=self.deployment_name,
            messages=message if isinstance(message,list) else [{"role": "user", "content": message}],
            max_tokens=self.max_tokens,
            stream=is_stream,
            temperature=self.temperature,
            top_p=self.top_p,
            frequency_penalty=self.frequency_penalty,
            presence_penalty=self.presence_penalty,
            stop=self.stop
        )
        self._update_usage_stats(response)
        if is_stream:
            return self._handle_streaming_response(response)
        else:
            return response['choices'][0]['text']

    def image_chat(self, message: str, image_path: str, max_tokens: int = 1000) -> str:
        with Image.open(image_path) as img:
            resized_img = self._resize_image(img)
            buffered = io.BytesIO()
            resized_img.save(buffered, format=resized_img.format or "JPEG")
            base64_image = base64.b64encode(buffered.getvalue()).decode('utf-8')

        image_message = {
            "role": "user", 
            "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}},
                {"type": "text", "text": message}
            ]
        }
        self.history.append(image_message)

        response = self.client.chat.completions.create(
            model=self.deployment_name,
            messages=self.history,
            max_tokens=max_tokens,
            temperature=self.temperature,
            top_p=self.top_p,
            frequency_penalty=self.frequency_penalty,
            presence_penalty=self.presence_penalty,
            stop=self.stop
        )

        assistant_message = response.choices[0].message.content
        self.history.append({"role": "assistant", "content": assistant_message})
        self.stat["call_count"]["image_chat"] += 1
        self._update_usage_stats(response)
        return assistant_message

    def _resize_image(self, img: Image.Image) -> Image.Image:
        original_width, original_height = img.size
        original_aspect_ratio = original_width / original_height

        closest_size = min(self.supported_sizes, 
                           key=lambda size: abs(size[0]/size[1] - original_aspect_ratio))

        resized_img = img.resize(closest_size, Image.LANCZOS)
        return resized_img

    def CodeRunner(self, code: str) -> str:
        # 删除代码开头和结尾的 ```python 标记
        code = code.strip()
        if code.startswith("```python"):
            code = code[9:]
        if code.endswith("```"):
            code = code[:-3]
        code = code.strip()

        # 重定向标准输出到缓冲区
        stdout_buffer = io.StringIO()
        with contextlib.redirect_stdout(stdout_buffer):
            try:
                # 执行代码
                exec(code)
                output = stdout_buffer.getvalue()

                # 如果没有打印输出，获取最后一个表达式的值
                if output.strip() == "":
                    tree = ast.parse(code)
                    if isinstance(tree.body[-1], ast.Expr):
                        last_expr = compile(ast.Expression(tree.body[-1].value), '<string>', 'eval')
                        output = str(eval(last_expr))

            except Exception as e:
                output = f"发生错误: {str(e)}"

        return output

    def tool_chat(self, user_message: str, tools: List[Dict[str, Any]], function_module: Any, is_stream: bool = False) -> Union[str, Iterator[str]]:
        iterator = ContinuousStreamIterator(self, user_message, tools, function_module, self.max_tokens, is_stream)
        
        if is_stream:
            return (chunk for chunk in iterator if chunk is not None)
        else:
            return "".join(chunk for chunk in iterator if chunk is not None)

    def one_tool_chat(self, user_message: str, tools: List[Dict[str, Any]], function_module: Any, max_tokens: int = 4000) -> str:
        response = self.client.chat.completions.create(
            model=self.deployment_name,
            messages=[{"role": "user", "content": user_message}],
            max_tokens=max_tokens,
            functions=tools,
            temperature=self.temperature,
            top_p=self.top_p,
            frequency_penalty=self.frequency_penalty,
            presence_penalty=self.presence_penalty,
            stop=self.stop
        )

        assistant_message = response.choices[0].message.content or ""
        function_call = response.choices[0].message.function_call

        self._update_usage_stats(response)

        if function_call:
            function_name = function_call.name
            function_args = function_call.arguments

            if function_name == "CodeRunner":
                tool_result = self.CodeRunner(function_args)
            elif hasattr(function_module, function_name):
                function = getattr(function_module, function_name)
                try:
                    tool_result = self._call_function(function, function_args)
                except Exception as e:
                    tool_result = f"Error executing {function_name}: {str(e)}"
            else:
                tool_result = f"Function {function_name} not found in the provided module."

            final_response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "user", "content": user_message},
                    {"role": "assistant", "content": assistant_message},
                    {"role": "function", "name": function_name, "content": str(tool_result)},
                    {"role": "user", "content": "根据工具执行结果，继续对话。"}
                ],
                max_tokens=max_tokens
            )

            final_assistant_message = final_response.choices[0].message.content
            self._update_usage_stats(final_response)
            self.stat["call_count"]["tool_chat"] += 1
            return f"*初次响应:* {assistant_message}\n*使用工具:* {function_name}({function_args})\n*工具反馈:* {tool_result}\n*最终结果:* {final_assistant_message}"
        else:
            self.stat["call_count"]["tool_chat"] += 1
            return assistant_message
        
    def _call_function(self, function, function_args):
        if isinstance(function_args, dict):
            return function(**function_args)
        elif isinstance(function_args, str):
            # 如果是字符串，尝试解析为 JSON，如果失败则作为单个参数传递
            try:
                parsed_args = json.loads(function_args)
                if isinstance(parsed_args, dict):
                    return function(**parsed_args)
                else:
                    return function(parsed_args)
            except json.JSONDecodeError:
                return function(function_args)
        else:
            # 如果既不是字典也不是字符串，直接作为单个参数传递
            return function(function_args)
        
    def get_history(self) -> List[Dict[str, Any]]:
        return self.history

    def clear_chat(self) -> None:
        self.history.clear()

    def get_stats(self) -> Dict[str, int]:
        return self.stat
    
    def audio_chat(self, message: str, audio_path: str) -> str:
        raise NotImplementedError("Azure OpenAI does not support audio input.")
    
    def video_chat(self, message: str, video_path: str) -> str:
        raise NotImplementedError("Azure OpenAI does not support video input.")
    

class ContinuousStreamIterator:
    def __init__(self, client, initial_message, tools, function_module, max_tokens, is_stream):
        self.client = client
        self.history = [{"role": "user", "content": initial_message}]
        self.tools = tools
        self.function_module = function_module
        self.max_tokens = max_tokens
        self.is_stream = is_stream
        self.current_response = None
        self.tool_uses = []
        self.state = 'initial_response'
        self.buffer = []
        self.assistant_message = ""
        self.initial_response_complete = False

    def __iter__(self):
        return self

    def __next__(self):
        while True:
            if self.buffer:
                return self.buffer.pop(0)

            if self.state == 'initial_response':
                self._handle_initial_response()
            elif self.state == 'tool_calls':
                self._handle_tool_calls()
            elif self.state == 'final_response':
                self._handle_final_response()
            elif self.state == 'finished':
                raise StopIteration
            else:
                raise StopIteration

    def _handle_initial_response(self):
        if not self.current_response:
            self.current_response = self.client.client.chat.completions.create(
                model=self.client.deployment_name,
                max_tokens=self.max_tokens,
                messages=self.history,
                tools=self.tools,
                stream=self.is_stream,
                temperature=self.client.temperature,
                top_p=self.client.top_p,
                frequency_penalty=self.client.frequency_penalty,
                presence_penalty=self.client.presence_penalty,
                stop=self.client.stop
            )
        
        if self.is_stream:
            try:
                event = next(self.current_response)
                self._process_event(event)
            except StopIteration:
                self._finalize_initial_response()
        else:
            for content in self.current_response.content:
                if content.type == 'text':
                    self.assistant_message += content.text
                    self.buffer.append(content.text)
                elif content.type == 'tool_calls':
                    self.tool_uses.extend(content.tool_calls)
            self._finalize_initial_response()

    def _finalize_initial_response(self):
        self.initial_response_complete = True
        self.history.append({"role": "assistant", "content": self.assistant_message})
        if self.tool_uses:
            self.state = 'tool_calls'
        else:
            self.state = 'final_response'
        self.current_response = None

    def _handle_tool_calls(self):
        if self.tool_uses:
            tool_call = self.tool_uses.pop(0)
            function_args=None
            function_name = tool_call.name
            try:
                if not tool_call.input:
                    function_args = {}
                else:
                    function_args = json.loads(tool_call.input)
            except AttributeError:
                function_name = "unknown"
                function_args = {}

            if hasattr(self.function_module, function_name):
                function = getattr(self.function_module, function_name)
                try:
                    tool_result = function(**function_args)
                    tool_result = self.client.process_tool_result(tool_result)
                except Exception as e:
                    tool_result = f"Error executing {function_name}: {str(e)}"
            else:
                tool_result = f"Function {function_name} not found in the provided module."

            tool_result_message = f"\n使用工具: {function_name}\n参数: {function_args}\n工具结果: {tool_result}\n"
            self.history.append({"role": "user", "content": tool_result_message})
            self.buffer.append(tool_result_message)
        else:
            self.state = 'final_response'

    def _handle_final_response(self):
        if not self.current_response:
            self.current_response = self.client.client.chat.completions.create(
                model=self.client.deployment_name,
                max_tokens=self.max_tokens,
                messages=self.history,
                stream=self.is_stream,
            temperature=self.client.temperature,
            top_p=self.client.top_p,
            frequency_penalty=self.client.frequency_penalty,
            presence_penalty=self.client.presence_penalty,
            stop=self.client.stop
            )
        
        if self.is_stream:
            try:
                event = next(self.current_response)
                self._process_event(event)
            except StopIteration:
                self.state = 'finished'
        else:
            content = "".join([c.text for c in self.current_response.content if c.type == 'text'])
            self.buffer.append(content)
            self.state = 'finished'

    def _process_event(self, event):
        for choice in event.choices:
            delta = choice.delta
            if delta.content:
                self.assistant_message += delta.content
                self.buffer.append(delta.content)
            if delta.function_call:
                self.tool_uses.append(delta.function_call)
            elif choice.finish_reason == 'stop':
                if not self.initial_response_complete:
                    self._finalize_initial_response()
