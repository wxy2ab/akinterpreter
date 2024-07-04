from typing import List, Dict, Any, Optional
import requests
import json
from ._llm_api_client import LLMApiClient
from ..utils.config_setting import Config
from typing import Literal

class ErnieApiClient(LLMApiClient):
    def __init__(self, api_key: str = None, secret_key: str = None, api_name: Literal["ernie-4.0-8k-latest","ernie-4.0-turbo-8k"] = "ernie-4.0-turbo-8k"):
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
        self.chat_history = []
        self.system = None
        self.temperature = 0.8
        self.top_p = 1
        self.max_output_tokens = 1024

    def get_access_token(self):
        url = f"https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={self.api_key}&client_secret={self.secret_key}"
        response = requests.post(url)
        data = response.json()
        self.access_token = data.get("access_token")
        return self.access_token

    def send_request(self, messages, functions=None, record_history=True, use_full_messages=False):
        if not self.access_token:
            self.get_access_token()

        full_messages = self.chat_history + messages if use_full_messages else messages

        if full_messages[-1]["role"] == "user" and record_history:
            self.chat_history.append(full_messages[-1])

        payload = {
            "messages": full_messages,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "max_output_tokens": self.max_output_tokens
        }

        if self.system is not None:
            payload["system"] = self.system

        if functions is not None:
            payload["functions"] = functions

        payload = json.dumps(payload)

        full_url = f"{self.base_url}?access_token={self.access_token}"
        headers = {'Content-Type': 'application/json'}
        response = requests.post(full_url, headers=headers, data=payload)
        response_data = response.json()

        usage = response_data.get('usage', {})
        self.chat_statistics['total_tokens'] += usage.get('total_tokens', 0)
        self.chat_statistics['call_times'] += 1

        if record_history:
            if 'result' in response_data:
                self.chat_history.append({
                    "role": "assistant",
                    "content": response_data['result']
                })
            elif 'function_call' in response_data:
                self.chat_history.append({
                    "role": "assistant",
                    "content": None,
                    "function_call": response_data['function_call']
                })

        if response_data.get('need_clear_history', False):
            half_length = len(self.chat_history) // 2
            self.chat_history = self.chat_history[half_length:]

        return response_data

    def text_chat(self, message: str) -> str:
        messages = [{"role": "user", "content": message}]
        response = self.send_request(messages, record_history=True, use_full_messages=True)
        return response.get("result", "")

    def one_chat(self, message: str) -> str:
        messages = [{"role": "user", "content": message}]
        response = self.send_request(messages, record_history=False)
        return response.get("result", "")

    def tool_chat(self, user_message: str, tools: List[Dict[str, Any]], function_module: Any) -> str:
        result = []
        converted_tools = self.convert_format(tools)

        messages = [{"role": "user", "content": user_message}]
        response_data = self.send_request(messages, functions=converted_tools, record_history=True, use_full_messages=True)

        if 'function_call' in response_data:
            tool_content = response_data['function_call']['thoughts']
            tool_name = response_data['function_call']['name']
            tool_args = json.loads(response_data['function_call']['arguments'])

            result.append(tool_content)
            if tool_name == "CodeRunner":
                result.append(tool_args["code"])

            if hasattr(function_module, tool_name):
                tool_func = getattr(function_module, tool_name)
                tool_output = tool_func(**tool_args)
            else:
                tool_output = f"Error: Function {tool_name} not found in the provided module."

            messages.append({
                "role": "assistant",
                "content": None,
                "function_call": {
                    "name": tool_name,
                    "arguments": response_data['function_call']['arguments']
                }
            })
            messages.append({
                "role": "function",
                "name": tool_name,
                "content": json.dumps({"result_value": tool_output}, ensure_ascii=False)
            })

            if tool_name == "CodeRunner":
                result.append(f"运行结果:{tool_output}")

            response_data = self.send_request(messages, functions=converted_tools, record_history=True, use_full_messages=True)

        if "result" in response_data:
            result.append(response_data["result"])
        else:
            result.append(str(response_data))

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
        self.chat_history = []

    def get_stats(self) -> Dict[str, Any]:
        return self.chat_statistics

    def image_chat(self, message: str, image_path: str) -> str:
        raise NotImplementedError("Ernie API does not support image chat.")

    def audio_chat(self, message: str, audio_path: str) -> str:
        raise NotImplementedError("Ernie API does not support audio chat.")

    def video_chat(self, message: str, video_path: str) -> str:
        raise NotImplementedError("Ernie API does not support video chat.")