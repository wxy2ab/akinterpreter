from .moonshot_client import MoonShotClient
from ..utils.config_setting import Config
from ._llm_api_client import LLMApiClient

class InfinityDeepSeekClient(LLMApiClient):
    pass




class InfinityDeepSeekClient(MoonShotClient):
    def __init__(self, model: str = "deepseek-v3"):
        base_url = "https://cloud.infini-ai.com/maas/v1"

        config = Config()


        api_key = config.get("infinity_api_key")
        super().__init__(api_key, base_url, max_tokens=8192)
        if model is None or model == "":

            model = "deepseek-v3"
        self.model = model