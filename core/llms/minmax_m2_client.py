
from .moonshot_client import MoonShotClient
from ..utils.config_setting import Config
from ._llm_api_client import LLMApiClient



class MinMaxM2Client(LLMApiClient):
    pass


class MinMaxM2Client(MoonShotClient):
    def __init__(self, model: str = "MiniMax-M2"):
        base_url = "https://api.minimax.chat/v1"
        config = Config()

        api_key = config.get("minimax_api_key")
        super().__init__(api_key, base_url, max_tokens=8192)
        if model is None or model == "":
            model = "MiniMax-M2"
        self.model = model