from typing import Generator, Union, Dict, Any
from ..llms.llm_factory import LLMFactory
from ..llms._llm_api_client import LLMApiClient
from ..planner.akshare_fun_planner import AkshareFunPlanner
from ._talker import Talker

class CliTalker(Talker):
    def __init__(self):
        factory = LLMFactory()
        self.llm_client: LLMApiClient = factory.get_instance()
        self.akshare_planner = AkshareFunPlanner()
        self.use_akshare = False

    def chat(self, message: str) -> Generator[Union[str, Dict[str, Any]], None, None]:
        if not self.use_akshare:
            # 只在第一次判断是否是金融数据查询
            self.use_akshare = self._is_financial_data_query(message)

        if self.use_akshare:
            # 如果已经确定使用AkshareSSEPlanner，就继续使用它
            yield from self.akshare_planner.plan_chat(message)
        else:
            # 否则，继续使用LLM API响应
            yield from self.llm_client.text_chat(message, is_stream=True)

    def clear(self) -> None:
        self.llm_client.clear_chat()
        self.use_akshare = False  # 重置状态
        # 如果AkshareSSEPlanner有清理方法，也应该在这里调用
        # self.akshare_planner.clear()

    def get_llm_client(self) -> LLMApiClient:
        return self.llm_client

    def set_llm_client(self, llm_client: LLMApiClient) -> None:
        self.llm_client = llm_client

    def _is_financial_data_query(self, query: str) -> bool:
        """
        使用LLM来判断查询是否与金融数据相关。
        """
        prompt = f"""请判断以下查询是否与金融数据（非金融知识）相关。
        只回答"是"或"否"。

        查询: {query}

        是否与金融数据相关？"""

        response = self.llm_client.one_chat(prompt)
        return "是" in response.lower()