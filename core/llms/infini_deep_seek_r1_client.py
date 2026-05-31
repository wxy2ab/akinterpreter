from .moonshot_client import MoonShotClient
from ..utils.config_setting import Config
from ._llm_api_client import LLMApiClient

class InfinityDeepSeekR1Client(LLMApiClient):
    pass


class InfinityDeepSeekR1Client(MoonShotClient):
    def __init__(self, model: str = "deepseek-r1"):
        base_url = "https://cloud.infini-ai.com/maas/v1"

        config = Config()

        api_key = config.get("infinity_api_key")
        super().__init__(api_key, base_url, max_tokens=4096)
        if model is None or model == "":
            model = "deepseek-r1"
        self.model = model