from typing import List, Dict, Any, Literal, Optional
import openai
import json
from ._llm_api_client import LLMApiClient
from ..utils.config_setting import Config

class DeepSeekClient(LLMApiClient):
    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.deepseek.com/", model: Literal["deepseek-chat", "deepseek-coder"] = "deepseek-chat"):
        config = Config()
        if api_key is None and config.has_key("deep_seek_api_key"):
            api_key = config.get("deep_seek_api_key")
        self.client = openai.OpenAI(api_key=api_key, base_url=base_url)
        self.messages = []
        self.task = "通用对话"
        self.model = model
        self.temperature = 1.0
        self.stats = {
            "total_tokens": 0,
            "completion_tokens": 0,
            "prompt_tokens": 0,
            "total_cost": 0.0,
            "num_chats": 0,
        }

    def one_chat(self, message: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": message}],
            temperature=self.temperature,
        )
        self._update_stats(response)
        return response.choices[0].message.content

    def text_chat(self, message: str) -> str:
        self.messages.append({"role": "user", "content": message})
        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.messages,
            temperature=self.temperature,
        )
        assistant_message = response.choices[0].message.content
        self.messages.append({"role": "assistant", "content": assistant_message})
        self._update_stats(response)
        return assistant_message

    def tool_chat(self, user_message: str, tools: List[Dict[str, Any]], function_module: Any) -> str:
        self.messages.append({"role": "user", "content": user_message})
        response = self._send_tool_request(self.messages, tools)
        assistant_output = response.choices[0].message

        if 'tool_calls' in assistant_output:
            tool_call = assistant_output.tool_calls[0]
            tool_name = tool_call['function']['name']
            tool_args = json.loads(tool_call['function']['arguments'])
            tool_args = tool_args["properties"]

            if hasattr(function_module, tool_name) and callable(getattr(function_module, tool_name)):
                tool_func = getattr(function_module, tool_name)
                tool_output = tool_func(**tool_args)
                tool_msg = {"name": tool_name, "role": "tool", "content": tool_output}
                self.messages.append(tool_msg)

                second_response = self._send_tool_request(self.messages, tools)
                final_output = second_response.choices[0].message['content']
                self.messages.append(second_response.choices[0].message)
            else:
                final_output = f"未找到名为 {tool_name} 的工具函数。"
        else:
            final_output = assistant_output['content']

        self._update_stats(response)
        return final_output

    def _send_tool_request(self, messages, tools):
        return self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            functions=tools,
            function_call="auto",
            temperature=self.temperature,
        )

    def set_task(self, task: str, model: Optional[str] = None) -> None:
        if task == "代码":
            self.model = "deepseek-coder"
            self.temperature = 0.0
        elif task == "数据分析":
            self.model = "deepseek-chat"
            self.temperature = 0.7
        elif task == "对话":
            self.model = "deepseek-chat"
            self.temperature = 1.0
        elif task == "翻译":
            self.model = "deepseek-chat"
            self.temperature = 1.1
        elif task == "创意":
            self.model = "deepseek-chat"
            self.temperature = 1.25
        else:
            raise ValueError("不支持的任务类型")

        if model is not None:
            self.model = model
        self.task = task
        self.messages = []

    def _update_stats(self, response):
        self.stats["total_tokens"] += response.usage.total_tokens
        self.stats["completion_tokens"] += response.usage.completion_tokens
        self.stats["prompt_tokens"] += response.usage.prompt_tokens
        self.stats["total_cost"] += response.usage.total_tokens * 0.002 / 1000
        self.stats["num_chats"] += 1

    def get_stats(self) -> Dict[str, Any]:
        return self.stats

    def clear_chat(self) -> None:
        self.messages = []

    def image_chat(self, message: str, image_path: str) -> str:
        raise NotImplementedError("DeepSeek API does not support image chat.")

    def audio_chat(self, message: str, audio_path: str) -> str:
        raise NotImplementedError("DeepSeek API does not support audio chat.")

    def video_chat(self, message: str, video_path: str) -> str:
        raise NotImplementedError("DeepSeek API does not support video chat.")