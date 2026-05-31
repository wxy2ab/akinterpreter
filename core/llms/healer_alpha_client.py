from .moonshot_client import MoonShotClient
from ..utils.config_setting import Config
from ._llm_api_client import LLMApiClient

class HealerAlphaClient(LLMApiClient):
    pass

class HealerAlphaClient(MoonShotClient):
    def __init__(self, model: str = "openrouter/healer-alpha"):
        base_url = "https://openrouter.ai/api/v1"
        config = Config()
        api_key = config.get("openrouter_api_key")
        super().__init__(api_key, base_url, max_tokens=64000)
        if model is None or model == "":
            model = "openrouter/healer-alpha"
        self.model = model
