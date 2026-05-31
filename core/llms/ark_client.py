from .moonshot_client import MoonShotClient
from ..utils.config_setting import Config
from ._llm_api_client import LLMApiClient

class ArkClient(LLMApiClient):
    pass

class ArkClient(MoonShotClient):
    def __init__(self, model: str = "ark-code-latest"):
        base_url = "https://ark.cn-beijing.volces.com/api/coding/v3"
        config = Config()
        api_key = config.get("ark_coding_key")
        super().__init__(api_key, base_url, max_tokens=None)
        if model is None or model == "":
            model = "ark-code-latest"
        self.model = model
