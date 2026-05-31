from .moonshot_client import MoonShotClient
from ..utils.config_setting import Config
from ._llm_api_client import LLMApiClient

class HunterAlphaClient(LLMApiClient):
    pass

class HunterAlphaClient(MoonShotClient):
    def __init__(self, model: str = "openrouter/hunter-alpha"):
        base_url = "https://openrouter.ai/api/v1"
        config = Config()
        api_key = config.get("openrouter_api_key")
        super().__init__(api_key, base_url, max_tokens=64000)
        if model is None or model == "":
            model = "openrouter/hunter-alpha"
        self.model = model
