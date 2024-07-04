import ast
import contextlib
import io
import json
import mimetypes
import os
from typing import Any, Dict, List, Union
from vertexai.preview.generative_models import GenerativeModel, Part, Tool, GenerationConfig
import vertexai
from google.oauth2 import service_account
from ._llm_api_client import LLMApiClient
from ..utils.config_setting import Config

#众所周知，这个类在一定范围内是运行不了的
#想运行这个库，应该开启proxy 设置
#不过这个api目前版本智能程度一般，你未必想用


class GeminiAPIClient(LLMApiClient):

    def __init__(self, project_id, location):
        # 获取项目根目录的路径
        root_dir = self.find_project_root()

        # 构建服务账号 JSON 文件的完整路径
        service_account_path = os.path.join(root_dir, "wxy2ab.json")

        config = Config()
        if config.has_key("service_account_path"):
            service_account_path = config.get("service_account_path")

        if not os.path.exists(service_account_path):
            raise FileNotFoundError("Could not find service account JSON file")
        
        if config.has_key("project_id"):
            project_id = config.get("project_id")
        
        if config.has_key("location"):
            location = config.get("location")

        # 从服务账号 JSON 文件创建凭证
        credentials = service_account.Credentials.from_service_account_file(
            service_account_path,
            scopes=["https://www.googleapis.com/auth/cloud-platform"])

        vertexai.init(project=project_id,
                      location=location,
                      credentials=credentials)
        self.model = GenerativeModel("gemini-1.5-pro-preview-0409")
        self.chat = self.model.start_chat()
        self.function_calls = 0
        self.total_tokens = 0
        self.history = []
        self.stat = {"call_count": {"tool_chat": 0}, "total_tokens": 0}
        self.generation_config = GenerationConfig(temperature=0.7,
                                                  top_k=40,
                                                  max_output_tokens=1000)

    @staticmethod
    def find_project_root(start_dir=None):
        """
        查找项目根目录。
        
        这个方法从给定的起始目录（默认为当前工作目录）开始，
        逐级向上查找，直到找到包含 'wxy2ab.json' 文件的目录，
        或者到达文件系统的根目录。

        :param start_dir: 开始搜索的目录，默认为当前工作目录
        :return: 项目根目录的路径
        :raises FileNotFoundError: 如果找不到项目根目录
        """
        if start_dir is None:
            start_dir = os.getcwd()

        current_dir = os.path.abspath(start_dir)
        while True:
            if os.path.exists(os.path.join(current_dir, "wxy2ab.json")):
                return current_dir
            parent_dir = os.path.dirname(current_dir)
            if parent_dir == current_dir:  # 已经到达文件系统的根目录
                raise FileNotFoundError(
                    "Could not find project root containing 'wxy2ab.json'")
            current_dir = parent_dir

    def _add_to_history(self, role: str, content: str):
        self.history.append({"role": role, "content": content})

    def _get_chat_history(self):
        return self.history

    def text_chat(self, message: str):
        self.function_calls += 1
        self._add_to_history("user", message)
        response = self.chat.send_message(
            message, generation_config=self.generation_config)
        self._update_metadata(response)
        self._add_to_history("assistant", response.text)
        return response.text

    def tool_chat(self, user_message: str, tools: List[Dict[str, Any]],
                  function_module: Any) -> str:
        self._add_to_history("user", user_message)

        # 将tools转换为Vertex AI的Tool格式
        vertex_tools = [Tool.from_dict(tool) for tool in tools]

        response = self.chat.send_message(
            user_message,
            tools=vertex_tools,
            generation_config=self.generation_config)
        self._update_metadata(response)
        assistant_message = response.text
        function_call = response.candidates[0].content.parts[
            -1] if response.candidates[0].content.parts else None

        self._add_to_history("assistant", assistant_message)
        self._update_usage_stats(response)

        if function_call and isinstance(function_call, Tool):
            function_name = function_call.function.name
            function_args = function_call.function.args

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

            self._add_to_history("function",
                                 f"{function_name}: {str(tool_result)}")

            final_response = self.chat.send_message(
                f"Function {function_name} returned: {tool_result}",
                generation_config=self.generation_config)
            self._update_metadata(final_response)
            final_assistant_message = final_response.text
            self._add_to_history("assistant", final_assistant_message)
            self.stat["call_count"]["tool_chat"] += 1
            return f"*Initial response:* {assistant_message}\n*Function call:* {function_name}({function_args})\n*Function result:* {tool_result}\n*Final response:* {final_assistant_message}"
        else:
            self.stat["call_count"]["tool_chat"] += 1
            return assistant_message

    def _call_function(self, function, function_args):
        if isinstance(function_args, dict):
            return function(**function_args)
        elif isinstance(function_args, str):
            try:
                parsed_args = json.loads(function_args)
                if isinstance(parsed_args, dict):
                    return function(**parsed_args)
                else:
                    return function(parsed_args)
            except json.JSONDecodeError:
                return function(function_args)
        else:
            return function(function_args)

    def CodeRunner(self, code: str) -> str:
        code = code.strip()
        if code.startswith("```python"):
            code = code[9:]
        if code.endswith("```"):
            code = code[:-3]
        code = code.strip()

        stdout_buffer = io.StringIO()
        with contextlib.redirect_stdout(stdout_buffer):
            try:
                exec(code)
                output = stdout_buffer.getvalue()

                if output.strip() == "":
                    tree = ast.parse(code)
                    if isinstance(tree.body[-1], ast.Expr):
                        last_expr = compile(
                            ast.Expression(tree.body[-1].value), '<string>',
                            'eval')
                        output = str(eval(last_expr))

            except Exception as e:
                output = f"发生错误: {str(e)}"

        return output

    def _update_usage_stats(self, response):
        self.stat["total_tokens"] += response.usage.total_tokens

    def clear_chat(self):
        self.chat = self.model.start_chat()
        self.history = []

    def get_stats(self):
        return self.stat

    def image_chat(self, message: str, image_path: str):
        self.function_calls += 1
        image = Part.from_image(image_path)
        self._add_to_history("user", f"{message} [Image: {image_path}]")
        response = self.chat.send_message(
            [message, image], generation_config=self.generation_config)
        self._update_metadata(response)
        self._add_to_history("assistant", response.text)
        return response.text

    def audio_chat(self, message: str, audio_path: str):
        self.function_calls += 1
        mime_type, _ = mimetypes.guess_type(audio_path)
        if mime_type is None:
            mime_type = "audio/mpeg"  # Default MIME type, adjust as needed

        with open(audio_path, "rb") as audio_file:
            audio_data = audio_file.read()

        audio = Part.from_data(data=audio_data, mime_type=mime_type)
        self._add_to_history("user", f"{message} [Audio: {audio_path}]")
        response = self.chat.send_message([message, audio])
        self._update_metadata(response)
        self._add_to_history("assistant", response.text)
        return response.text

    def video_chat(self, message: str, video_path: str):
        self.function_calls += 1
        mime_type, _ = mimetypes.guess_type(video_path)
        if mime_type is None:
            mime_type = "video/mp4"  # Default MIME type, adjust as needed

        with open(video_path, "rb") as video_file:
            video_data = video_file.read()

        video = Part.from_data(data=video_data, mime_type=mime_type)
        self._add_to_history("user", f"{message} [Video: {video_path}]")
        response = self.chat.send_message([message, video])
        self._update_metadata(response)
        self._add_to_history("assistant", response.text)
        return response.text

    def clear_chat(self):
        self.chat = self.model.start_chat()
        self.history.clear()

    def get_chat_history(self):
        return self._get_chat_history()

    def one_chat(self, message: Union[str, List[Union[str, Part]]]) -> str:
        """
        执行单次对话，不发送或记录历史记录。

        :param message: 可以是字符串消息或包含消息和多模态部分的列表
        :return: 助手的响应文本
        """
        try:
            # 创建一个新的聊天实例，以确保不使用任何历史记录
            temp_chat = self.model.start_chat()

            response = temp_chat.send_message(
                message, generation_config=self.generation_config)

            self._update_metadata(response)

            return response.text
        except Exception as e:
            error_message = f"Error in one_chat: {str(e)}"
            print(error_message)
            return error_message

    def _update_metadata(self, response):
        try:
            if hasattr(response, 'usage_metadata'):
                metadata = response.usage_metadata
                self.stat["total_tokens"] += getattr(metadata,
                                                     'total_token_count', 0)
                self.stat["prompt_token_count"] = getattr(
                    metadata, 'prompt_token_count', 0)
                self.stat["candidate_token_count"] = getattr(
                    metadata, 'candidate_token_count', 0)

                # Update total_tokens for backwards compatibility
                self.total_tokens = self.stat["total_tokens"]

                print(
                    f"Usage Metadata: Total Tokens: {self.stat['total_tokens']}, "
                    f"Prompt Tokens: {self.stat['prompt_token_count']}, "
                    f"Candidate Tokens: {self.stat['candidate_token_count']}")
            else:
                print(
                    "Warning: Response does not have usage_metadata attribute."
                )
        except Exception as e:
            print(f"Error updating usage metadata: {str(e)}")

    def set_generation_config(self,
                              temperature=0.7,
                              top_p=1,
                              top_k=40,
                              max_output_tokens=1000):
        """
        设置生成配置参数。
    
        :param temperature: 控制随机性的温度参数
        :param top_p: 用于核采样的累积概率阈值
        :param top_k: 用于采样的最高概率标记数
        :param max_output_tokens: 生成的最大标记数
        """
        self.generation_config = GenerationConfig(
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            max_output_tokens=max_output_tokens)
