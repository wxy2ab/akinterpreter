from typing import Any, Dict, Optional

from core.llms._llm_api_client import LLMApiClient
from core.llms.simple_deep_seek_client import SimpleDeepSeekClient
from ..utils.config_setting import Config

class SimpleDeepSeekClientReasoning(LLMApiClient):
    pass

class SimpleDeepSeekClientReasoning(SimpleDeepSeekClient):
    def __init__(
        self,
        model: str = "deepseek-v4-pro",
        max_tokens: int = 64000,
        temperature: float = 1.0,
        top_p: float = 1,
        presence_penalty: float = 0,
        frequency_penalty: float = 0,
        stop=None,
        reasoning_effort: Optional[str] = "high",
        extra_body: Optional[Dict[str, Any]] = None,
        thinking: bool = True,
    ):
        config = Config()
        api_key = config.get("deep_seek_api_key")
        super().__init__(
            api_key=api_key,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            presence_penalty=presence_penalty,
            frequency_penalty=frequency_penalty,
            stop=stop,
            reasoning_effort=reasoning_effort,
            extra_body=extra_body,
            thinking=thinking,
        )