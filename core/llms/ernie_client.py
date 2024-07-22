from typing import Iterator, List, Dict, Any, Optional, Union
import requests
import json
from ._llm_api_client import LLMApiClient
from ..utils.config_setting import Config
from typing import Literal
from ..utils.handle_max_tokens import handle_max_tokens

class ErnieApiClient(LLMApiClient):
    def __init__(self, 
                 api_key: str = None, 
                 secret_key: str = None, 
                 api_name: Literal["ernie-4.0-8k-latest", "ernie-4.0-turbo-8k"] = "ernie-4.0-turbo-8k",
                 temperature: float = 0.8,
                 top_p: float = 0.8,
                 penalty_score: float = 1.0,
                 stop: Optional[List[str]] = None,
                 max_output_tokens: int = 2048):
        config = Config()
        if config.has_key("ERNIE_API_KEY"):
            api_key = config.get("ERNIE_API_KEY")
        if config.has_key("ERNIE_SERCRET_KEY"):
            secret_key = config.get("ERNIE_SERCRET_KEY")
        
        self.api_key = api_key
        self.secret_key = secret_key
        self.api_name = api_name
        self.access_token = None
        self.base_url = f"https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/{api_name}"
        self.chat_statistics = {'total_tokens': 0, "call_times": 0}
        self.history = []
        self.system = None
        self.temperature = temperature
        self.top_p = top_p
        self.penalty_score = penalty_score
        self.stop = stop
        self.max_output_tokens = max_output_tokens

    def get_access_token(self):
        url = f"https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={self.api_key}&client_secret={self.secret_key}"
        response = requests.post(url)
        data = response.json()
        self.access_token = data.get("access_token")
        return self.access_token

    def send_request(self, messages, functions=None, record_history=True, use_full_messages=False, stream=False):
        if not self.access_token:
            self.get_access_token()
        full_messages = None
        if use_full_messages:
            self.history.extend(messages)
            full_messages = self.history
        else:
            full_messages = messages

        payload = {
            "messages": full_messages,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "penalty_score": self.penalty_score,
            "stop": self.stop,
            "max_output_tokens": self.max_output_tokens,
            "stream": stream
        }

        if self.system is not None:
            payload["system"] = self.system

        if functions is not None:
            payload["functions"] = functions

        payload = json.dumps(payload)

        full_url = f"{self.base_url}?access_token={self.access_token}"
        headers = {'Content-Type': 'application/json'}
        response = requests.post(full_url, headers=headers, data=payload, stream=stream)

        if stream:
            return response
        else:
            response_data = response.json()
            self._update_stats(response_data)
            return response_data

    def _update_stats(self, response_data):
        usage = response_data.get('usage', {})
        self.chat_statistics['total_tokens'] += usage.get('total_tokens', 0)
        self.chat_statistics['call_times'] += 1

    def _process_stream(self, response) -> Iterator[str]:
        full_response = ""
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data:'):
                    data = json.loads(line[5:])
                    if 'result' in data:
                        text = data['result']
                        full_response += str(text)
                        yield text
                    if data.get('is_end', False):
                        self._update_stats(data)
                        break
        self.history.append({"role": "assistant", "content": full_response})

    @handle_max_tokens
    def text_chat(self, message: str, is_stream: bool = False) -> Union[str, Iterator[str]]:
        messages = [{"role": "user", "content": message}]
        if is_stream:
            response = self.send_request(messages, record_history=True, use_full_messages=True, stream=True)
            return self._process_stream(response)
        else:
            response = self.send_request(messages, record_history=True, use_full_messages=True)
            return response.get("result", "")

    def one_chat(self, message: str, is_stream: bool = False) -> Union[str, Iterator[str]]:
        messages = [{"role": "user", "content": message}]
        if is_stream:
            response = self.send_request(messages, record_history=False, stream=True)
            return self._process_stream(response)
        else:
            response = self.send_request(messages, record_history=False)
            return response.get("result", "")

    def tool_chat(self, user_message: str, tools: List[Dict[str, Any]], function_module: Any, is_stream: bool = False) -> Union[str, Iterator[str]]:
        converted_tools = self.convert_format(tools)
        messages = [{"role": "user", "content": user_message}]

        def process_tool_call(function_call):
            tool_name = function_call['name']
            tool_args = json.loads(function_call['arguments'])
            
            if hasattr(function_module, tool_name):
                tool_func = getattr(function_module, tool_name)
                tool_output = tool_func(**tool_args)
            else:
                tool_output = f"Error: Function {tool_name} not found in the provided module."

            assistant_message = {
                "role": "assistant",
                "content": None,
                "function_call": {
                    "name": tool_name,
                    "arguments": function_call['arguments']
                }
            }
            function_message = {
                "role": "function",
                "name": tool_name,
                "content": json.dumps({"result_value": tool_output}, ensure_ascii=False)
            }
            
            messages.extend([assistant_message, function_message])

            return f"使用工具: {tool_name}\n参数: {tool_args}\n工具结果: {tool_output}\n"

        if is_stream:
            def stream_generator():
                response = self.send_request(messages, functions=converted_tools, record_history=False, use_full_messages=False, stream=True)
                full_response = ""
                for line in response.iter_lines():
                    if line:
                        line = line.decode('utf-8')
                        if line.startswith('data:'):
                            data = json.loads(line[5:])
                            if 'result' in data or 'thoughts' in data:
                                content = data['result'] if 'result' in data else data['thoughts']
                                yield content
                                full_response += content
                            if 'function_call' in data:
                                full_response = data
                            if data.get('is_end', False):
                                self._update_stats(data)
                                break

                try:
                    response_data = full_response
                    if isinstance(response_data, str):
                        response_data = json.loads(response_data)
                    if 'function_call' in response_data:
                        tool_result = process_tool_call(response_data['function_call'])
                        yield tool_result
                        
                        # Send a follow-up request
                        second_response = self.send_request(messages, functions=converted_tools, record_history=False, use_full_messages=False, stream=True)
                        for line in second_response.iter_lines():
                            if line:
                                line = line.decode('utf-8')
                                if line.startswith('data:'):
                                    data = json.loads(line[5:])
                                    if 'result' in data:
                                        yield data['result']
                                    if data.get('is_end', False):
                                        self._update_stats(data)
                                        break
                    else:
                        messages.append({"role": "assistant", "content": full_response})
                except json.JSONDecodeError:
                    messages.append({"role": "assistant", "content": full_response})

            return stream_generator()
        else:
            response_data = self.send_request(messages, functions=converted_tools, record_history=False, use_full_messages=False)
            result = []
            
            if 'function_call' in response_data:
                tool_result = process_tool_call(response_data['function_call'])
                result.append(tool_result)
                
                second_response = self.send_request(messages, functions=converted_tools, record_history=False, use_full_messages=False)
                result.append(second_response.get("result", ""))
                messages.append({"role": "assistant", "content": second_response.get("result", "")})
            else:
                result.append(response_data.get("result", ""))
                messages.append({"role": "assistant", "content": response_data.get("result", "")})

            # Update chat history after the entire conversation
            self.history.extend(messages)

            return "\n".join(result)

    def convert_format(self, input_data):
        output_data = []
        for item in input_data:
            function_data = item["function"]
            output_item = {
                "name": function_data["name"],
                "description": function_data["description"],
                "parameters": function_data.get("parameters", {})
            }
            output_data.append(output_item)
        return output_data

    def set_parameters(self, system=None, temperature=0.8, top_p=1, max_output_tokens=1024):
        self.system = system
        self.temperature = temperature
        self.top_p = top_p
        self.max_output_tokens = max_output_tokens

    def clear_chat(self) -> None:
        self.history = []

    def get_stats(self) -> Dict[str, Any]:
        return self.chat_statistics

    def image_chat(self, message: str, image_path: str) -> str:
        raise NotImplementedError("Ernie API does not support image chat.")

    def audio_chat(self, message: str, audio_path: str) -> str:
        raise NotImplementedError("Ernie API does not support audio chat.")

    def video_chat(self, message: str, video_path: str) -> str:
        raise NotImplementedError("Ernie API does not support video chat.")