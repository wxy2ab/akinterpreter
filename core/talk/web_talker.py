import asyncio
from datetime import datetime
import json
from typing import Generator, Union, Dict, Any


from ..llms.llm_factory import LLMFactory
from ..llms._llm_api_client import LLMApiClient
from ..planner.akshare_fun_planner import AkshareFunPlanner
from ._talker import Talker
from  ..sse.sse_message_queue import SSEMessageQueue
from  ..session.user_session_manager import UserSessionManager

class WebTalker(Talker):
    def __init__(self):
        factory = LLMFactory()
        self.llm_client: LLMApiClient = factory.get_instance()
        self.akshare_planner = AkshareFunPlanner()
        self.use_akshare = False
        self.message_queue = SSEMessageQueue()
        self.chat_history = []
        self.sessions = UserSessionManager()
        self.loop = self._get_or_create_event_loop()

    def chat(self, message: str) -> Generator[Union[str, Dict[str, Any]], None, None]:
        self.chat_history.append({"role":"user","content":message})
        self.sessions.update_chat_history(self.session_id, self.chat_history)
        self.sessions.update_last_request_time(self.session_id)
        if not self.use_akshare:
            # 只在第一次判断是否是金融数据查询
            self.use_akshare = self._is_financial_data_query(message)
        generator = None
        if self.use_akshare:
            # 如果已经确定使用AkshareSSEPlanner，就继续使用它
            generator = self.akshare_planner.plan_chat(message)
        else:
            # 否则，继续使用LLM API响应
            generator = self.llm_client.text_chat(message, is_stream=True)
        
        yield from self._process_generator(generator)
    def _process_generator(self, generator) -> Generator[str, None, None]:
        replies = []
        for chunk in generator:
            if "content" in chunk:
                replies.append(chunk["content"])
            yield chunk
        reply = ''.join(replies)
        self.chat_history.append({"role": "assistant", "content": reply})
        self.sessions.update_chat_history(self.session_id, self.chat_history)

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

    def set_session_id(self, session_id: str) -> None:
        self.session_id = session_id
        self.akshare_planner.add_plan_change_listener(self._on_plan_change)
        self.akshare_planner.add_code_change_listener(self._on_code_change)

    def _get_or_create_event_loop(self):
        try:
            return asyncio.get_running_loop()
        except RuntimeError:  # No running event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop
        
    def _on_plan_change(self, plan: dict) -> None:

        asyncio.run_coroutine_threadsafe(
            self.message_queue.put(self.session_id, {"type": "plan", "plan": plan}),
            self.loop
        )
        self.sessions.update_current_plan(self.session_id ,plan)
    
    def _on_code_change(self,step_codes:dict) -> None:

        asyncio.run_coroutine_threadsafe(
            self.message_queue.put(self.session_id, {"type": "code", "step_codes": step_codes}),
            self.loop
        )
        self.sessions.update_step_codes(self.session_id,step_codes=step_codes)