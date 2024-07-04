from typing import List, Dict, Any, Optional, Union
from openai import OpenAI
from pathlib import Path
import json
from ._llm_api_client import LLMApiClient
from ..utils.config_setting import Config

class MoonShotClient(LLMApiClient):
    def __init__(self, api_key: str = "", base_url: str = "https://api.moonshot.cn/v1"):
        config = Config()
        if api_key == "" and config.has_key("moonshot_api_key"):
            api_key = config.get("moonshot_api_key")
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.chat_count = 0
        self.token_count = 0
        self.messages = []
        self._model_list = ["moonshot-v1-128k", "moonshot-v1-8k", "moonshot-v1-32k"]
        self.model = self._model_list[0]

    def set_system_message(self, system_message: str = "你是一个智能助手,擅长把复杂问题清晰明白通俗易懂地解答出来"):
        self.messages = [{"role": "system", "content": system_message}]

    def text_chat(self, message: str) -> str:
        if not self.messages:
            self.set_system_message()

        self.messages.append({"role": "user", "content": message})

        completion = self.client.chat.completions.create(
            model=self.model,
            messages=self.messages,
            temperature=0.3
        )
        response = completion.choices[0].message.content

        self.messages.append({"role": "assistant", "content": response})

        self._update_stats(completion.usage)
        return response

    def one_chat(self, message: str) -> str:
        if not self.messages:
            self.set_system_message()

        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": message}],
            temperature=0.3
        )
        response = completion.choices[0].message.content

        self._update_stats(completion.usage)
        return response

    def tool_chat(self, user_message: str, tools: List[Dict[str, Any]], function_module: Any) -> str:
        if not self.messages:
            self.set_system_message()

        self.messages.append({"role": "user", "content": user_message})

        completion = self.client.chat.completions.create(
            model=self.model,
            messages=self.messages,
            tools=tools,
            temperature=0.3
        )
        assistant_output = completion.choices[0].message
        self._update_stats(completion.usage)

        if hasattr(assistant_output, 'tool_calls') and len(assistant_output.tool_calls) != 0:
            self.messages.append({"role": "assistant", "content": assistant_output.content, "tool_calls": assistant_output.tool_calls})
        else:
            self.messages.append({"role": "assistant", "content": assistant_output.content})

        assistant_replies = [assistant_output.content]

        if hasattr(assistant_output, 'tool_calls') and len(assistant_output.tool_calls) != 0:
            tool_calls = assistant_output.tool_calls

            for tool_call in tool_calls:
                tool_id = tool_call.id
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)

                if hasattr(function_module, tool_name) and callable(getattr(function_module, tool_name)):
                    tool_func = getattr(function_module, tool_name)
                    tool_output = tool_func(**tool_args)
                    tool_msg = {"name": tool_name, "role": "tool", "content": tool_output, "tool_call_id": tool_id}
                    self.messages.append(tool_msg)
                else:
                    return f"未找到名为 {tool_name} 的工具函数。"

            second_response = self._send_tool_request(self.messages, tools)
            final_output = second_response.choices[0].message.content

            assistant_replies.append(final_output)
        else:
            final_output = assistant_output.content

        return "\n".join(assistant_replies)

    def _send_tool_request(self, messages: List[Dict], tools: List[Dict]):
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
            temperature=0.3
        )
        self._update_stats(completion.usage)
        return completion

    def _update_stats(self, usage: Dict):
        self.chat_count += 1
        self.token_count += usage.total_tokens

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_chats": self.chat_count,
            "total_tokens": self.token_count
        }

    def clear_chat(self) -> None:
        self.messages = []

    def image_chat(self, message: str, image_path: str) -> str:
        raise NotImplementedError("MoonShot API does not support image chat.")

    def audio_chat(self, message: str, audio_path: str) -> str:
        raise NotImplementedError("MoonShot API does not support audio chat.")

    def video_chat(self, message: str, video_path: str) -> str:
        raise NotImplementedError("MoonShot API does not support video chat.")