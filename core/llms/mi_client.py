
from .moonshot_client import MoonShotClient
from ..utils.config_setting import Config
from ._llm_api_client import LLMApiClient



class MiClient(LLMApiClient):
    pass


class MiClient(MoonShotClient):
    def __init__(self, model: str = "mimo-v2-pro",thinking: bool = True):
        base_url = "https://api.xiaomimimo.com/v1/chat/completions"
        config = Config()

        api_key = config.get("mi_key")
        super().__init__(api_key, base_url, thinking)
        if model is None or model == "":
            model = "mimo-v2-pro"
        self.model = model