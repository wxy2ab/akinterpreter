
from .moonshot_client import MoonShotClient
from ..utils.config_setting import Config
from ._llm_api_client import LLMApiClient

class PPioGeminiProClient(LLMApiClient):
    pass


class PPioGeminiProClient(MoonShotClient):
    def __init__(self, model: str = "gemini-2.5-pro-preview-06-05"):
        base_url = "https://api.ppinfra.com/openai"
        config = Config()

        api_key = config.get("ppio_api_key")
        super().__init__(api_key, base_url, max_tokens=8192)
        if model is None or model == "":
            model = "gemini-2.5-pro-preview-06-05"
        self.model = model
