import ast
import contextlib
from typing import List, Dict, Any, Optional
from openai import AzureOpenAI
import os
import base64
from PIL import Image
import io
import json
from ._llm_api_client import LLMApiClient

class AzureGPT4oClient(LLMApiClient):
    def __init__(self, 
                 api_key: Optional[str] = None,
                 azure_endpoint: Optional[str] = None,
                 deployment_name: str = "gpt-4o",
                 api_version: str = "2023-05-15"):
        from ..utils.config_setting import Config
        config  =   Config()

        self.api_key = api_key or config.get("AZURE_OPENAI_API_KEY")
        self.azure_endpoint = azure_endpoint or config.get("AZURE_OPENAI_ENDPOINT")
        self.deployment_name = deployment_name
        self.api_version = api_version
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
        usage = response.usage
        self.stat["total_input_tokens"] += usage.prompt_tokens
        self.stat["total_output_tokens"] += usage.completion_tokens
        # Cost calculation would depend on your specific Azure pricing

    def text_chat(self, message: str, max_tokens: int = 1000) -> str:
        self.history.append({"role": "user", "content": message})
        response = self.client.chat.completions.create(
            model=self.deployment_name,
            messages=self.history,
            max_tokens=max_tokens
        )
        assistant_message = response.choices[0].message.content
        self.history.append({"role": "assistant", "content": assistant_message})
        self.stat["call_count"]["text_chat"] += 1
        self._update_usage_stats(response)
        return assistant_message

    def one_chat(self, message: str, max_tokens: int = 1000) -> str:
        response = self.client.chat.completions.create(
            model=self.deployment_name,
            messages=[{"role": "user", "content": message}],
            max_tokens=max_tokens
        )
        assistant_message = response.choices[0].message.content
        self.stat["call_count"]["text_chat"] += 1
        self._update_usage_stats(response)
        return assistant_message

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
            max_tokens=max_tokens
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

    def tool_chat(self, user_message: str, tools: List[Dict[str, Any]], function_module: Any, max_tokens: int = 1000) -> str:
        self.history.append({"role": "user", "content": user_message})
        response = self.client.chat.completions.create(
            model=self.deployment_name,
            messages=self.history,
            max_tokens=max_tokens,
            functions=tools
        )

        assistant_message = response.choices[0].message.content or ""
        function_call = response.choices[0].message.function_call

        self.history.append({"role": "assistant", "content": assistant_message})
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

            self.history.append({"role": "function", "name": function_name, "content": str(tool_result)})

            final_response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=self.history,
                max_tokens=max_tokens
            )

            final_assistant_message = final_response.choices[0].message.content
            self.history.append({"role": "assistant", "content": final_assistant_message})
            self._update_usage_stats(final_response)
            self.stat["call_count"]["tool_chat"] += 1
            return f"*Initial response:* {assistant_message}\n*Function call:* {function_name}({function_args})\n*Function result:* {tool_result}\n*Final response:* {final_assistant_message}"
        else:
            self.stat["call_count"]["tool_chat"] += 1
            return assistant_message

    def one_tool_chat(self, user_message: str, tools: List[Dict[str, Any]], function_module: Any, max_tokens: int = 1000) -> str:
        response = self.client.chat.completions.create(
            model=self.deployment_name,
            messages=[{"role": "user", "content": user_message}],
            max_tokens=max_tokens,
            functions=tools
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