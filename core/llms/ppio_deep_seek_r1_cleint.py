from .moonshot_client import MoonShotClient
from ..utils.config_setting import Config
from ._llm_api_client import LLMApiClient

class PPioDeepSeekR1Client(LLMApiClient):
    pass


class PPioDeepSeekR1Client(MoonShotClient):
    def __init__(self, model: str = "deepseek/deepseek-v3.2-exp"):
        base_url = "https://api.ppinfra.com/openai"
        config = Config()

        api_key = config.get("ppio_api_key")
        super().__init__(api_key, base_url, max_tokens=65536)
        if model is None or model == "":
            model = "deepseek/deepseek-v3.2-exp"
        self.model = model
        self.enable_thinking = True
