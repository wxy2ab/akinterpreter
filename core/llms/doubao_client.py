from typing import List, Dict, Any, Optional, Tuple
from ._llm_api_client import LLMApiClient
from ..utils.config_setting import Config
from volcenginesdkarkruntime import Ark

class DoubaoApiClient(LLMApiClient):
    def __init__(self):
        config = Config()
        self.api_key = config.get("volcengine_api_key")
        self.model = config.get("volcengine_doubao")
        
        # 使用自定义配置初始化 Ark 客户端
        self.client = Ark(api_key=self.api_key)
        
        self.history: List[Dict[str, str]] = []
        self.stats: Dict[str, int] = {
            "call_count": {"text_chat": 0, "image_chat": 0, "tool_chat": 0},
            "total_tokens": 0
        }

    def text_chat(self, message: str, max_tokens: int = 1000) -> str:
        self.history.append({"role": "user", "content": message})
        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.history,
            max_tokens=max_tokens
        )
        assistant_message = response.choices[0].message.content
        self.history.append({"role": "assistant", "content": assistant_message})
        self.stats["call_count"]["text_chat"] += 1
        self.stats["total_tokens"] += response.usage.total_tokens
        return assistant_message

    def image_chat(self, message: str, image_path: str) -> str:
        import base64
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')

        content = [
            {"type": "text", "text": message},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
        ]
        self.history.append({"role": "user", "content": content})
        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.history
        )
        assistant_message = response.choices[0].message.content
        self.history.append({"role": "assistant", "content": assistant_message})
        self.stats["call_count"]["image_chat"] += 1
        self.stats["total_tokens"] += response.usage.total_tokens
        return assistant_message

    def tool_chat(self, user_message: str, tools: List[Dict[str, Any]], function_module: Any) -> str:
        raise NotImplementedError("Tool chat is not implemented for DoubaoApiClient")

    def one_chat(self, message: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": message}]
        )
        assistant_message = response.choices[0].message.content
        self.stats["call_count"]["text_chat"] += 1
        self.stats["total_tokens"] += response.usage.total_tokens
        return assistant_message

    def clear_chat(self):
        self.history.clear()

    def get_stats(self) -> Dict[str, Any]:
        return self.stats

    def audio_chat(self, message: str, audio_path: str) -> str:
        raise NotImplementedError("Audio chat is not supported by DoubaoApiClient")

    def video_chat(self, message: str, video_path: str) -> str:
        raise NotImplementedError("Video chat is not supported by DoubaoApiClient")