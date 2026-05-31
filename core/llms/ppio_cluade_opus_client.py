
from .moonshot_client import MoonShotClient
from ..utils.config_setting import Config
from ._llm_api_client import LLMApiClient

class PPioClaudeOpusClient(LLMApiClient):
    pass


class PPioClaudeOpusClient(MoonShotClient):
    def __init__(self, model: str = "pa/claude-opus-4-5-20251101"):
        base_url = "https://api.ppinfra.com/openai"
        config = Config()

        api_key = config.get("ppio_api_key")
        super().__init__(api_key, base_url, max_tokens=128000)
        if model is None or model == "":
            model = "pa/claude-opus-4-5-20251101"
        self.model = model
