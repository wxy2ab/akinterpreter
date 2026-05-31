from .moonshot_client import MoonShotClient
from ..utils.config_setting import Config
from ._llm_api_client import LLMApiClient

class TencentDeepSeekR1Client(LLMApiClient):
    pass




class TencentDeepSeekR1Client(MoonShotClient):
    def __init__(self, model: str = "deepseek-r1"):
        base_url = "https://api.lkeap.cloud.tencent.com/v1"


        config = Config()

        api_key = config.get("tencent_api_key")
        super().__init__(api_key, base_url, max_tokens=8196)
        if model is None or model == "":

            model = "deepseek-r1"
        self.model = model
