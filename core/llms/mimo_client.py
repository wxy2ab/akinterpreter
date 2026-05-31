from .moonshot_client import MoonShotClient
from ..utils.config_setting import Config
from ._llm_api_client import LLMApiClient

class MimoClient(LLMApiClient):
    pass

class MimoClient(MoonShotClient):
    def __init__(self, model: str = "mimo-v2.5-pro"):
        base_url = "https://token-plan-cn.xiaomimimo.com/v1"
        config = Config()
        api_key = config.get("mimo_api_key")
        super().__init__(api_key, base_url, max_tokens=None)
        if model is None or model == "":
            model = "mimo-v2.5-pro"
        self.model = model
