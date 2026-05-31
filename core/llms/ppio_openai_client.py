
from .moonshot_client import MoonShotClient
from ..utils.config_setting import Config
from ._llm_api_client import LLMApiClient

class PPioOpenAIClient(LLMApiClient):
    pass


class PPioOpenAIClient(MoonShotClient):
    def __init__(self, model: str = "pa/p3"):
        base_url = "https://api.ppinfra.com/openai"
        config = Config()

        api_key = config.get("ppio_api_key")
        super().__init__(api_key, base_url, max_tokens=8192)
        if model is None or model == "":
            model = "pa/p3"
        self.model = model
