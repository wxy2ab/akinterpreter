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
    def __init__(self, llm_factory: LLMFactory):
        self.llm_factory = llm_factory
        self.llm_client: LLMApiClient = self.llm_factory.get_instance()
        self.current_plan: Optional[Dict[str, Any]] = None
        self.execution_results: List[Dict[str, Any]] = []

    @abstractmethod
    def get_retrieval_provider(self) -> RetrievalProvider:
        """返回一个RetrievalProvider实例，提供数据检索相关的信息"""
        pass

    @abstractmethod
    def plan_chat(self, query: str) -> Generator[Dict[str, Any], None, None]:
        """
        与用户进行多轮对话，生成并修改计划
        yield 格式: {"type": "plan", "content": plan_dict} 或 {"type": "message", "content": message_str}
        """
        pass

    @abstractmethod
    def confirm_plan(self) -> None:
        """确认当前计划，准备执行"""
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
    def execute_code(self, code: str) -> Dict[str, Any]:
        """执行给定的代码并返回结果"""
        pass

    @abstractmethod
    def stream_progress(self) -> Generator[Dict[str, Any], None, None]:
        """
        流式输出整个过程的进度信息
        yield 格式: {"step": int, "total_steps": int, "description": str, "progress": float}
        """
        pass

    @abstractmethod
    def get_final_report(self) -> Generator[str, None, None]:
        """生成并流式输出最终报告"""
        pass

    @abstractmethod
    def handle_error(self, error: Exception) -> Generator[Dict[str, Any], None, None]:
        """
        处理执行过程中的错误
        yield 格式: {"type": "error", "content": error_message}
        """
        pass

    @abstractmethod
    def reset(self) -> None:
        """重置计划器状态"""
        pass

    @abstractmethod
    def save_state(self) -> Dict[str, Any]:
        """保存当前状态"""
        pass

    @abstractmethod
    def load_state(self, state: Dict[str, Any]) -> None:
        """加载保存的状态"""
        pass