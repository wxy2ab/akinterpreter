from .moonshot_client import MoonShotClient
from ..utils.config_setting import Config
from ._llm_api_client import LLMApiClient

class OpenRouterClient(LLMApiClient):
    pass

class OpenRouterClient(MoonShotClient):
    def __init__(self, model: str = "openai/gpt-4o-2024-11-20"):
        base_url = "https://openrouter.ai/api/v1"
        config = Config()
        api_key = config.get("openrouter_api_key")
        super().__init__(api_key, base_url, max_tokens=16000)
        if model is None or model == "":
            model = "openai/gpt-4o-2024-11-20"
        self.model = model
