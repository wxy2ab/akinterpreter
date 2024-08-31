import logging
from typing import Union, List, Dict, Any, Iterator
from ._llm_api_client import LLMApiClient

class FallbackLLMClient(LLMApiClient):
    def __init__(self, main_llm: str = "MiniMaxProClient", auxiliary_llms: str = "SimpleDeepSeekClient,GLMClient"):
        self.main_llm = main_llm
        self.auxiliary_llms = auxiliary_llms
        self.llm_factory = None
        self.llms = None
        self.logger = logging.getLogger(__name__)

    def _lazy_init(self):
        if self.llms is None:
            from .llm_factory import LLMFactory
            self.llm_factory = LLMFactory()
            self.llms = [self.llm_factory.get_instance(self.main_llm)]
            self.llms.extend([self.llm_factory.get_instance(llm.strip()) for llm in self.auxiliary_llms.split(',')])

    def _execute_with_fallback(self, method_name: str, *args, **kwargs):
        self._lazy_init()
        for i, llm in enumerate(self.llms):
            try:
                method = getattr(llm, method_name)
                return method(*args, **kwargs)
            except Exception as e:
                self.logger.warning(f"{type(llm).__name__} failed: {str(e)}")
                if i == len(self.llms) - 1:
                    raise Exception("All LLMs failed")

    def one_chat(self, message: Union[str, List[Union[str, Any]]], is_stream: bool = False) -> Union[str, Iterator[str]]:
        return self._execute_with_fallback("one_chat", message, is_stream)

    def text_chat(self, message: str, is_stream: bool = False) -> Union[str, Iterator[str]]:
        return self._execute_with_fallback("text_chat", message, is_stream)

    def tool_chat(self, user_message: str, tools: List[Dict[str, Any]], function_module: Any, is_stream: bool = False) -> Union[str, Iterator[str]]:
        return self._execute_with_fallback("tool_chat", user_message, tools, function_module, is_stream)

    def audio_chat(self, message: str, audio_path: str) -> str:
        return self._execute_with_fallback("audio_chat", message, audio_path)

    def video_chat(self, message: str, video_path: str) -> str:
        return self._execute_with_fallback("video_chat", message, video_path)

    def clear_chat(self):
        self._lazy_init()
        for llm in self.llms:
            llm.clear_chat()

    def get_stats(self) -> Dict[str, Any]:
        self._lazy_init()
        stats = {}
        for i, llm in enumerate(self.llms):
            stats[f"LLM_{i}"] = llm.get_stats()
        return stats