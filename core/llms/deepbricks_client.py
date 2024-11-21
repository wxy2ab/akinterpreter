from .moonshot_client import MoonShotClient
from ..utils.config_setting import Config
from ._llm_api_client import LLMApiClient

class DeepBricksClient(LLMApiClient):
    pass

class DeepBricksClient(MoonShotClient):
    def __init__(self, model: str = "gpt-4o"):
        base_url = "https://api.deepbricks.ai/v1/"
        config = Config()
        api_key = config.get("deepbricks_api_key")
        super().__init__(api_key, base_url, max_tokens=4096)
        if model is None or model == "":
            model = "gpt-4o"
        self.model = model
