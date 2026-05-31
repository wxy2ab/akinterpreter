



from typing import Any, Dict, Iterator, List, Union
from core.llms._llm_api_client import LLMApiClient


class DummyClient(LLMApiClient):
    def one_chat(self, message: Union[str, List[Union[str, Any]]], is_stream: bool = False) -> Union[str, Iterator[str]]:
        return ""
    
    def text_chat(self, message: str, is_stream: bool = False) -> Union[str, Iterator[str]]:
        return ""

    def tool_chat(self, user_message: str, tools: List[Dict[str, Any]], function_module: Any, is_stream: bool = False) -> Union[str, Iterator[str]]:
        return ""

    def tool_invoke(self, messages: List[Dict[str, str]], tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        return {"content": "", "tool_calls": []}

    def audio_chat(self, message: str, audio_path: str) -> str:
        return ""

    def video_chat(self, message: str, video_path: str) -> str:
        return ""

    def get_stats(self) -> Dict[str, Any]:
        return {}
    
    def clear_chat(self):
        pass
