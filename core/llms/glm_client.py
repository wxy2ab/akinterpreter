from typing import List, Dict, Any,Literal
import requests
import json
from ._llm_api_client import LLMApiClient
from ..utils.config_setting import Config


class GLMClient(LLMApiClient):
    def __init__(self, api_key: str = "", base_url: str = "https://open.bigmodel.cn",model:Literal["glm-4-0520","glm-4" ,"glm-4-air","glm-4-airx", "glm-4-flash"]="glm-4-0520"):
        config  = Config()
        if api_key == "" and config.has_key("glm_api_key"):
            api_key = config.get("glm_api_key")
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        self.messages = []
        self.top_p = 0.7
        self.temperature = 0.5

    def set_system_message(self, system_message: str = "你是一个智能助手,擅长把复杂问题清晰明白通俗易懂地解答出来"):
        """设置系统消息,并清空之前的对话历史"""
        self.messages = [{"role": "system", "content": system_message}]

    def text_chat(self, message: str) -> str:
        if not self.messages:
            self.set_system_message()
        self.messages.append({"role": "user", "content": message})
        url = f"{self.base_url}/api/paas/v4/chat/completions"
        data = {
            "model": "glm-4",
            "messages": self.messages,
            "temperature": self.temperature,
            "top_p": self.top_p
        }
        response = requests.post(url, headers=self.headers, data=json.dumps(data))
        output = response.json()["choices"][0]["message"]["content"]
        self.messages.append({"role": "assistant", "content": output})
        return output

    def one_chat(self, message: str) -> str:
        url = f"{self.base_url}/api/paas/v4/chat/completions"
        data = {
            "model": "glm-4",
            "messages": [{"role": "user", "content": message}],
            "temperature": self.temperature,
            "top_p": self.top_p
        }
        response = requests.post(url, headers=self.headers, data=json.dumps(data))
        return response.json()["choices"][0]["message"]["content"]

    def tool_chat(self, user_message: str, tools: List[Dict[str, Any]], function_module: Any) -> str:
        self.messages.append({"role": "user", "content": user_message})
        url = f"{self.base_url}/api/paas/v4/chat/completions"
        data = {
            "model": "glm-4",
            "messages": self.messages,
            "tools": tools,
            "tool_choice": "auto",
            "temperature": self.temperature,
            "top_p": self.top_p
        }

        # 第一次请求
        response = requests.post(url, headers=self.headers, data=json.dumps(data))
        output = response.json()["choices"][0]["message"]
        if "tool_calls" in output:
            self.messages.append({"role": "assistant", "content": output["content"], "tool_calls": output["tool_calls"]})
        else:
            self.messages.append({"role": "assistant", "content": output["content"]})

        # 如果有tool调用,则进行第二次请求
        if "tool_calls" in output:
            for tool_call in output["tool_calls"]:
                tool_name = tool_call["function"]["name"]
                if hasattr(function_module, tool_name):
                    tool_func = getattr(function_module, tool_name)
                    tool_args = json.loads(tool_call["function"]["arguments"])
                    tool_output = tool_func(**tool_args)
                    tool_msg = {"role": "tool", "content": tool_output, "tool_call_id": tool_call["id"]}
                    self.messages.append(tool_msg)
                else:
                    error_msg = f"Function {tool_name} not found in the provided module."
                    self.messages.append({"role": "tool", "content": error_msg, "tool_call_id": tool_call["id"]})

            # 第二次请求
            data["messages"] = self.messages
            response = requests.post(url, headers=self.headers, data=json.dumps(data))
            output = response.json()["choices"][0]["message"]["content"]
            self.messages.append({"role": "assistant", "content": output})

        return output

    def clear_chat(self) -> None:
        self.messages = []

    def get_stats(self) -> Dict[str, Any]:
        # This method is not implemented in the original code.
        # You may want to add tracking for tokens, requests, etc.
        return {
            "total_messages": len(self.messages)
        }

    def image_chat(self, message: str, image_path: str) -> str:
        raise NotImplementedError("GLM API does not support image chat.")

    def audio_chat(self, message: str, audio_path: str) -> str:
        raise NotImplementedError("GLM API does not support audio chat.")

    def video_chat(self, message: str, video_path: str) -> str:
        raise NotImplementedError("GLM API does not support video chat.")