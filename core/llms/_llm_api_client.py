from abc import ABC, abstractmethod
from typing import Generator, List, Dict, Any, Union

class LLMApiClient(ABC):
    """用于LLM API客户端（例如Gemini）的抽象基类。"""

    @abstractmethod
    def text_chat(self, message: str, is_stream:bool = False) ->Union[ str ,Generator[str,None,None] ]:
        """处理文本消息并返回LLM的文本响应。"""
        pass

    @abstractmethod
    def tool_chat(self, user_message: str, tools: List[Dict[str, Any]], function_module: Any ,is_stream:bool = False) -> Union[ str ,Generator[str,None,None] ]:
        """
        处理可以访问外部工具的文本消息。

        - `tools`：工具规范列表（字典）。
        - `function_module`：包含要调用的工具函数的模块。
        """
        pass

    @abstractmethod
    def audio_chat(self, message: str, audio_path: str) -> str:
        """处理文本消息和音频文件，并返回LLM的文本响应。"""
        pass

    @abstractmethod
    def video_chat(self, message: str, video_path: str) -> str:
        """处理文本消息和视频文件，并返回LLM的文本响应。"""
        pass

    @abstractmethod
    def clear_chat(self):
        """清除聊天历史或上下文。"""
        pass

    @abstractmethod
    def one_chat(self, message: Union[str, List[Union[str, Any]]], is_stream:bool = False) -> Union[ str,Generator[str,None,None] ]:
        """执行单次聊天交互，不使用或存储聊天历史记录。"""
        pass

    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """返回使用情况统计信息（例如，token使用情况、API调用计数）。"""
        pass
