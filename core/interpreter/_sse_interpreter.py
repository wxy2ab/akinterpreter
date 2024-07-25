from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple, Union, Iterator, Generator

class SSEInterpreter(ABC):
    @abstractmethod
    def interpret(self, data: Any, user_request: str, is_stream: bool = False) -> Union[Tuple[str, str], Generator[str, None, None]]:
        """
        解释器
        
        Args:
            data (Any): 要解释的数据
            user_request (str): 用户请求
            is_stream (bool): 是否使用流式处理

        Returns:
            如果 is_stream 为 False，返回 Tuple[str, str]，表示 (代码, 报告)
            如果 is_stream 为 True，返回 Generator[str, None, None]，生成流式输出
        """
        pass

    @abstractmethod
    def generate_code(self, data: Any, user_request: str, is_stream: bool = False) -> Union[str, Generator[str, None, None]]:
        """
        生成代码
        
        Args:
            data (Any): 用于生成代码的数据
            user_request (str): 用户请求
            is_stream (bool): 是否使用流式处理

        Returns:
            如果 is_stream 为 False，返回 str，表示生成的代码
            如果 is_stream 为 True，返回 Generator[str, None, None]，生成流式代码输出
        """
        pass

    @abstractmethod
    def generate_report(self, data: Any, error: Any, user_request: str, is_stream: bool = False) -> Union[str, Generator[str, None, None]]:
        """
        生成报告
        
        Args:
            data (Any): 用于生成报告的数据
            error (Any): 错误信息（如果有）
            user_request (str): 用户请求
            is_stream (bool): 是否使用流式处理

        Returns:
            如果 is_stream 为 False，返回 str，表示生成的报告
            如果 is_stream 为 True，返回 Generator[str, None, None]，生成流式报告输出
        """
        pass

    @abstractmethod
    def process_sse_event(self, event: Dict[str, Any]) -> str:
        """
        处理单个 SSE 事件
        
        Args:
            event (Dict[str, Any]): SSE 事件数据

        Returns:
            str: 处理后的事件内容
        """
        pass

    @abstractmethod
    def handle_tool_call(self, tool_call: Dict[str, Any], function_module: Any) -> str:
        """
        处理工具调用
        
        Args:
            tool_call (Dict[str, Any]): 工具调用信息
            function_module (Any): 包含工具函数的模块

        Returns:
            str: 工具调用的结果
        """
        pass

    @abstractmethod
    def stream_processor(self, stream: Iterator[Dict[str, Any]]) -> Generator[str, None, None]:
        """
        处理 SSE 流
        
        Args:
            stream (Iterator[Dict[str, Any]]): SSE 事件流

        Yields:
            str: 处理后的流式输出
        """
        pass