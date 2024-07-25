from abc import ABC, abstractmethod
from typing import Generator, Dict, Any, List, Tuple, Optional
from ..llms.llm_factory import LLMFactory
from ..llms._llm_api_client import LLMApiClient

from abc import ABC, abstractmethod
from typing import Dict, List, Any

class RetrievalProvider(ABC):
    @abstractmethod
    def get_categories(self) -> Dict[str, str]:
        """
        返回可用的数据类别字典
        :return: 字典，键为类别名称，值为类别描述
        """
        pass

    @abstractmethod
    def get_functions(self, categories: List[str]) -> Dict[str, List[str]]:
        """
        根据给定的类别返回相关函数
        :param categories: 类别列表
        :return: 字典，键为类别，值为该类别下的函数列表
        """
        pass

    @abstractmethod
    def get_specific_doc(self, functions: List[str]) -> Dict[str, str]:
        """
        获取指定函数的文档
        :param functions: 函数名列表
        :return: 字典，键为函数名，值为对应的文档
        """
        pass

class SSEPlanner(ABC):
    @abstractmethod
    def plan_chat(self, query: str) -> Generator[Dict[str, Any], None, None]:
        """
        与用户进行多轮对话，生成并修改计划
        yield 格式: {"type": "plan", "content": plan_dict} 或 {"type": "message", "content": message_str}
        """
        pass

    @abstractmethod
    def step(self) -> Generator[Dict[str, Any], None, None]:
        """
        执行下一个步骤，包括代码生成、执行和错误修复
        yield 格式: {
            "type": "code_generation" | "code_execution" | "code_fix" | "result",
            "content": str_or_dict
        }
        """
        pass

    @abstractmethod
    def get_final_report(self) -> Generator[str, None, None]:
        """生成并流式输出最终报告"""
        pass