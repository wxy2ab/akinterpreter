from abc import ABC, abstractmethod
from typing import Generator, Any, Union, Dict
from ..llms._llm_api_client import LLMApiClient 

class Talker(ABC):
    @abstractmethod
    def chat(self, message: str) -> Generator[Union[str, Dict[str, Any]], None, None]:
        """
        与大语言模型进行对话,支持SSE(Server-Sent Events)。
        
        :param message: 用户输入的消息
        :return: 生成器,用于逐步返回模型的响应，可以是字符串或字典
        """
        pass

    @abstractmethod
    def clear(self) -> None:
        """
        清除对话历史或重置对话状态。
        """
        pass

    @abstractmethod
    def get_llm_client(self) -> LLMApiClient:
        """
        获取当前使用的LLM客户端实例。
        
        :return: LLMApiClient的实例
        """
        pass

    @abstractmethod
    def set_llm_client(self, llm_client: LLMApiClient) -> None:
        """
        设置要使用的LLM客户端实例。
        
        :param llm_client: LLMApiClient的实例
        """
        pass