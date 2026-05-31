from .moonshot_client import MoonShotClient
from ..utils.config_setting import Config
from ._llm_api_client import LLMApiClient

class QiniuDeepSeekR1Client(LLMApiClient):
    pass




class QiniuDeepSeekR1Client(MoonShotClient):
    def __init__(self, model: str = "deepseek-r1-0528"):
        base_url = "https://api.qnaigc.com/v1/"

        config = Config()

        api_key = config.get("qiniu_api_key")
        super().__init__(api_key, base_url, max_tokens=8192)
        if model is None or model == "":
            model = "deepseek-r1-0528"
        self.model = model


