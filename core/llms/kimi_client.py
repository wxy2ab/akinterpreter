
from .moonshot_client import MoonShotClient
from ..utils.config_setting import Config
from ._llm_api_client import LLMApiClient



class KimiClient(LLMApiClient):
    pass


class KimiClient(MoonShotClient):
    def __init__(self, model: str = "kimi-for-coding",thinking: bool = True):
        base_url = "https://api.kimi.com/coding/v1"
        config = Config()

        api_key = config.get("moonshot_api_key")
        super().__init__(api_key, base_url, thinking)
        if model is None or model == "":
            model = "kimi-for-coding"
        self.model = model