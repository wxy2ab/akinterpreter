import ast
import contextlib
import io
import json
import mimetypes
import os
import time
from typing import Any, Dict, List, Union, Iterator
from google.cloud import aiplatform
from google.protobuf.struct_pb2 import Value
from ._llm_api_client import LLMApiClient
from ..utils.config_setting import Config
import asyncio
import queue
import threading
from ..utils.log import logger as logging
from ..utils.handle_max_tokens import handle_max_tokens
from google.oauth2 import service_account
from google.cloud.aiplatform.v1.schema.predict.instance import ImageInstance, TextPrompt, VideoInstance, Content, Part
from google.cloud.aiplatform.gapic.schema import predict_instance

def convert_proto_struct_to_dict(struct):
    result = {}
    for key, value in struct.items():
        if isinstance(value, Value):
            if value.HasField('null_value'):
                result[key] = None
            elif value.HasField('number_value'):
                result[key] = value.number_value
            elif value.HasField('string_value'):
                result[key] = value.string_value
            elif value.HasField('bool_value'):
                result[key] = value.bool_value
            elif value.HasField('struct_value'):
                result[key] = convert_proto_struct_to_dict(value.struct_value)
            elif value.HasField('list_value'):
                result[key] = [convert_proto_value(v) for v in value.list_value.values]
            else:
                result[key] = value
        return result

def convert_proto_value(value):
    if value.HasField('null_value'):
        return None
    elif value.HasField('number_value'):
        return value.number_value
    elif value.HasField('string_value'):
        return value.string_value
    elif value.HasField('bool_value'):
        return value.bool_value
    elif value.HasField('struct_value'):
        return convert_proto_struct_to_dict(value.struct_value)
    elif value.HasField('list_value'):
        return [convert_proto_value(v) for v in value.list_value.values]
    return None

class GeminiAPIClient(LLMApiClient):

    def __init__(self, project_id="", location="us-central1"):

        # 获取项目根目录的路径
        root_dir = self.find_project_root()

        # 构建服务账号 JSON 文件的完整路径
        service_account_path = os.path.join(root_dir, "wxy2ab.json")

        config = Config()
        if config.has_key("service_account_path"):
            service_account_path = config.get("service_account_path")

        if config.has_key("project_id"):
            project_id = config.get("project_id")

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

        aiplatform.init(project=project_id,
                            location=location,
                            credentials=credentials)

        # 使用 Endpoint 方式
        endpoint_name = "projects/" + project_id + "/locations/" + location + "/endpoints/" + "your-endpoint-name"  # 替换为您的 Endpoint 名称
        self.endpoint = aiplatform.Endpoint(endpoint_name)

        self.function_calls = 0
        self.total_tokens = 0
        self.history = []
        self.stat = {"call_count": {"tool_chat": 0}, "total_tokens": 0}
        self.generation_config = {
            "temperature": 0.7,
            "top_k": 40,
            "max_output_tokens": 8000
        }

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

    @handle_max_tokens
    def text_chat(self, message: str, is_stream: bool = False) -> Union[str, Iterator[str]]:
        self.function_calls += 1
        self._add_to_history("user", message)

        if is_stream:
            return self._stream_response(message)
        else:
            response = self._predict(message)
            self._update_metadata(response)
            self._add_to_history("assistant", response["content"])
            return response["content"]


    def _add_to_history(self, role: str, content: str):
        self.history.append({"role": role, "content": content})

    def _get_chat_history(self):
        return self.history

    @handle_max_tokens
    def text_chat(self, message: str, is_stream: bool = False) -> Union[str, Iterator[str]]:
        self.function_calls += 1
        self._add_to_history("user", message)

        if is_stream:
            return self._stream_response(message)
        else:
            response = self.chat.send_message(message, generation_config=self.generation_config)
            self._update_metadata(response)
            self._add_to_history("assistant", response.text)
            return response.text

    def tool_chat(self, user_message: str, tools: List[Dict[str, Any]], function_module: Any, is_stream: bool = False) -> Union[str, Iterator[str]]:
        self._add_to_history("user", user_message)
        # 构建 Vertex AI 请求数据
        request = {
            "prompt": user_message,
            "tools": tools,
            "generation_config": self.generation_config
        }

        if is_stream:
            return self._stream_tool_chat(request, function_module)
        else:
            return self._non_stream_tool_chat(request, function_module)

    def _non_stream_tool_chat(self, request: dict, function_module: Any) -> str:
        response = self._predict(request)
        self._update_metadata(response)
        assistant_message = response["content"]
        function_call = response.get("function_call", None)

        self._add_to_history("assistant", assistant_message)
        self._update_usage_stats(response)

        if function_call:
            function_name = function_call["name"]
            function_args = function_call.get("args", {})

            tool_result = self._execute_function(function_name, function_args, function_module)

            final_response_request = {
                "prompt": f"Function {function_name} returned: {tool_result}",
                "generation_config": self.generation_config
            }
            final_response = self._predict(final_response_request)
            final_assistant_message = final_response["content"]
            self._add_to_history("assistant", final_assistant_message)
            self._update_metadata(final_response)

            return f"*Initial response:* {assistant_message}\n*Function call:* {function_name}({function_args})\n*Function result:* {tool_result}\n*Final response:* {final_assistant_message}"
        else:
            self.stat["call_count"]["tool_chat"] += 1
            return assistant_message

    def _stream_tool_chat(self, request: dict, function_module: Any) -> Iterator[str]:
        iterator = AsyncContentIterator()
        threading.Thread(target=self._stream_tool_chat_thread, args=(request, function_module, iterator)).start()
        return iterator

    def _stream_tool_chat_thread(self, request: dict, function_module: Any, iterator: "AsyncContentIterator"):
        try:
            responses = self.endpoint.predict(instances=[request], stream=True) # Streaming prediction
            for chunk in responses:
                if "predictions" in chunk and chunk["predictions"]: # New structure, use chunk["predictions"][0] if it is a list of predictions
                  prediction = chunk["predictions"][0]
                  if "function_call" in prediction:
                      self._process_function_call_from_chunk(prediction, function_module, iterator)
                  elif "content" in prediction:
                      iterator.add_content(prediction["content"])

                if "usage" in chunk: # Extract usage if exists
                  self._update_usage_stats(chunk)
        except Exception as e:
            logging.error(f"Error in tool_chat: {str(e)}", exc_info=True)
            iterator.add_content("An error occurred during processing. Please try again.")
        finally:
            iterator.mark_done()

    def _process_chunk(self, chunk, function_module, iterator):
        try:
            if self._has_function_call(chunk):
                self._process_function_call_from_chunk(chunk, function_module, iterator)
            elif self._has_text_content(chunk):
                iterator.add_content(chunk.text)
            self._update_metadata(chunk)
        except Exception as e:
            logging.warning(f"Error processing chunk: {str(e)}", exc_info=True)

    def _has_function_call(self, prediction):
        return "function_call" in prediction

    def _has_text_content(self, prediction):
        return "content" in prediction and bool(prediction["content"])
    
    def _process_function_call_from_chunk(self, prediction, function_module, iterator):
        try:
            function_call = prediction["function_call"]
            function_name = function_call.get('name', '') # Get safely function name
            function_args = self._safe_get_args(function_call)

            if not function_name:
                return

            self._stream_function_call_info(iterator, function_name, function_args)
            tool_result = self._execute_function(function_name, function_args, function_module)
            self._stream_function_result(iterator, tool_result)
            self._stream_final_response(function_name, tool_result, iterator)
        except Exception as e:
            logging.error(f"Error processing function call from chunk: {str(e)}", exc_info=True)
            iterator.add_content(f"Error processing function call: {str(e)}\n")
  
    def _safe_get_args(self, function_call): # Same logic, but working on new format
        args = function_call.get('args', None)
        if args is None:
            return {}

        try:
            if isinstance(args, dict):
                return args
            elif isinstance(args, str):
                try:
                    return json.loads(args)
                except json.JSONDecodeError:
                    return {"arg": args}
            return {"arg": str(args)}
        except Exception as e:
            logging.warning(f"Error converting function args: {str(e)}", exc_info=True)
            return {}

    def _process_function_call_from_chunk(self, chunk, function_module, iterator):
        try:
            function_call = chunk.candidates[0].content.parts[0].function_call
            function_name = getattr(function_call, 'name', '')
            function_args = self._safe_get_args(function_call)

            if not function_name:
                #logging.warning("Function name is empty")
                #iterator.add_content("Error: Function name is empty\n")
                return

            self._stream_function_call_info(iterator, function_name, function_args)
            tool_result = self._execute_function(function_name, function_args, function_module)
            self._stream_function_result(iterator, tool_result)
            self._stream_final_response(function_name, tool_result, iterator)
        except Exception as e:
            logging.error(f"Error processing function call from chunk: {str(e)}", exc_info=True)
            iterator.add_content(f"Error processing function call: {str(e)}\n")

    def _execute_function(self, function_name: str, function_args: Dict[str, Any], function_module: Any) -> Any:
        try:
            if function_name == "CodeRunner":
                return self.CodeRunner(function_args.get("code", ""))
            elif hasattr(function_module, function_name):
                function = getattr(function_module, function_name)
                return function(**function_args)
            else:
                error_msg = f"Function {function_name} not found in the provided module."
                logging.warning(error_msg)
                return error_msg
        except Exception as e:
            error_msg = f"Error executing {function_name}: {str(e)}"
            logging.error(error_msg, exc_info=True)
            return error_msg

    def _stream_function_call_info(self, iterator, function_name, function_args):
        args_str = ", ".join(f"{key}={value}" for key, value in function_args.items())
        iterator.add_content(f"\n*Function call:* {function_name}({args_str})\n")

    def _stream_function_result(self, iterator, tool_result):
        iterator.add_content("*Function result:* ")
        for char in str(tool_result):
            iterator.add_content(char)
            time.sleep(0.01)  # Simulate streaming for function result
        iterator.add_content("\n")

    def _stream_final_response(self, function_name, tool_result, iterator):
        try:
            for chunk in self.chat.send_message(f"Function {function_name} returned: {tool_result}", generation_config=self.generation_config, stream=True):
                if hasattr(chunk, 'text') and chunk.text:
                    iterator.add_content(chunk.text)
                self._update_metadata(chunk)
        except Exception as e:
            logging.error(f"Error in final response streaming: {str(e)}", exc_info=True)
            iterator.add_content("An error occurred while processing the final response.")

    def _execute_function2(self, function_name: str, function_args: Dict[str, Any], function_module: Any) -> Any:
        try:
            if function_name == "CodeRunner":
                return self.CodeRunner(function_args.get("code", ""))
            elif hasattr(function_module, function_name):
                function = getattr(function_module, function_name)
                return self._call_function(function, function_args)
            else:
                return f"Function {function_name} not found in the provided module."
        except Exception as e:
            logging.error(f"Error executing function {function_name}: {str(e)}", exc_info=True)
            return f"Error executing {function_name}: {str(e)}"

    def _call_function1(self, function, function_args):
        return function(**function_args)

    def _call_function(self, function, function_args):
        if len(function_args)==0:
                return function()
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

    def tool_invoke(self, messages: List[Dict[str, str]], tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        response = self._predict({
            "prompt": messages,
            "tools": tools,
            "generation_config": self.generation_config
        })
        function_call = response.get("function_call")
        tool_calls = []
        if function_call:
            tool_calls.append({
                "id": function_call.get("id", ""),
                "function": {
                    "name": function_call.get("name", ""),
                    "arguments": json.dumps(function_call.get("args", {}), ensure_ascii=False)
                }
            })
        return self._normalize_tool_invoke_response(response.get("content", "") or "", tool_calls)

    def _update_usage_stats(self, response):

      if "usage" in response:
        usage = response["usage"]
        self.stat["total_tokens"] += usage.get('total_tokens', 0) # changed to usage.get
        self.stat["prompt_token_count"] = usage.get('prompt_tokens', 0)
        self.stat["candidate_token_count"] = usage.get('completion_tokens', 0) # changed to completion_tokens
        self.total_tokens = self.stat["total_tokens"]

    def clear_chat(self):
        # No direct equivalent for clear_chat in new API per message history within a chat session.
        self.history = [] # Clear local history

    def get_stats(self):
        return self.stat

    def image_chat(self, message: str, image_path: str):
        try:
            with open(image_path, "rb") as image_file:
                image_bytes = image_file.read()
            image = Part(
                data=image_bytes,
                mime_type="image/jpeg" # 确保mime_type正确
            )

            request = {
              "prompt": TextPrompt(text=message),
              "image": ImageInstance(bytes_base64_encoded=image)

            }
            response = self._predict(request)
            return response.get("content", "No response content")


        except Exception as e:
            return f"Error processing image: {e}"


    def audio_chat(self, message: str, audio_path: str):
      try:
        mime_type, _ = mimetypes.guess_type(audio_path)
        if mime_type is None:
            mime_type = "audio/mpeg"

        with open(audio_path, "rb") as audio_file:
            audio_data = audio_file.read()
        audio = Part(data=audio_data, mime_type=mime_type)

        request = {
            "prompt": TextPrompt(text=message),
            "audio": audio
        }
        response = self._predict(request)
        return response.get("content", "No response content")
      except Exception as e:
        return f"Error processing audio: {e}"

    def video_chat(self, message: str, video_path: str):
      try:
        mime_type, _ = mimetypes.guess_type(video_path)
        if mime_type is None:
            mime_type = "video/mp4"
        with open(video_path, "rb") as video_file:
            video_data = video_file.read()

        video = Part(data=video_data, mime_type=mime_type)

        request = {
            "prompt": TextPrompt(text=message),
            "video": video
        }
        response = self._predict(request)
        return response.get("content", "No response content")
      except Exception as e:
        return f"Error processing video: {e}"

    def get_chat_history(self):
        return self._get_chat_history()

    def one_chat(self, message: Union[str, List[Union[str, Part]]], is_stream: bool = False) -> Union[str, Iterator[str]]:
        try:
            if is_stream:
                return self._stream_response(message) #流式调用保持不变
            else:
                response = self._predict({"prompt": message, "generation_config": self.generation_config}) #正确调用_predict
                return response["content"]
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

                # print(
                #     f"Usage Metadata: Total Tokens: {self.stat['total_tokens']}, "
                #     f"Prompt Tokens: {self.stat['prompt_token_count']}, "
                #     f"Candidate Tokens: {self.stat['candidate_token_count']}")
            else:
                print(
                    "Warning: Response does not have usage_metadata attribute."
                )
        except Exception as e:
            print(f"Error updating usage metadata: {str(e)}")

            temp_chat = self.model.start_chat()


    def _stream_response(self, message, chat=None, tools=None) -> Iterator[str]:
        request = {
            "prompt": message,
            "generation_config": self.generation_config,
            "tools": tools
        }

        responses = self.endpoint.predict(instances=[request], stream=True)
        full_response = ""
        for chunk in responses:
          if "predictions" in chunk and chunk["predictions"]:
            prediction = chunk["predictions"][0]
            if "content" in prediction:
                full_response += prediction["content"]
                yield prediction["content"]

        self.history.append({"role": "assistant", "content": full_response})

    def _predict(self, request):
        response = self.endpoint.predict(instances=[request])
        if response.predictions and isinstance(response.predictions[0], dict):
            return response.predictions[0]
        else:
          logging.warning(f"Unexpected prediction format {response.predictions}")
          return {"content": f"Unexpected prediction format {response.predictions}"}


class AsyncContentIterator(Iterator[str]):

    def __init__(self):
        self.queue = queue.Queue()
        self.is_done = False
        self.lock = threading.Lock()

    def add_content(self, content: str):
        self.queue.put(content)

    def mark_done(self):
        with self.lock:
            self.is_done = True
        self.queue.put(None)  # Sentinel to signal the end

    def __iter__(self):
        return self

    def __next__(self) -> str:
        item = self.queue.get()
        if item is None:
            raise StopIteration
        return item
#众所周知，这个类在一定范围内是运行不了的
#想运行这个库，应该开启proxy 设置
#不过这个api目前版本智能程度一般，你未必想用
#使用这个文件需要安装下面的库
#pip install google-cloud-aiplatform
