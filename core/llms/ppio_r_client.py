from .moonshot_client import MoonShotClient
from ..utils.config_setting import Config
from ._llm_api_client import LLMApiClient

class PPioRClient(LLMApiClient):
    pass


class PPioRClient(MoonShotClient):
    def __init__(self, model: str = "deepseek/deepseek-v3.1-terminus"):
        base_url = "https://api.ppinfra.com/openai"
        config = Config()

        api_key = config.get("ppio_api_key")
        super().__init__(api_key, base_url, max_tokens=8192)
        if model is None or model == "":
            model = "deepseek/deepseek-v3.1-terminus"
        self.model = model
        self.enable_thinking = True
