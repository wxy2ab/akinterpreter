from .moonshot_client import MoonShotClient
from ..utils.config_setting import Config
from ._llm_api_client import LLMApiClient

class VolcDeepSeekR1Client(LLMApiClient):
    pass


#deepseek-r1-250120
class VolcDeepSeekR1Client(MoonShotClient):
    def __init__(self, model: str = "deepseek-r1-250528"):
        base_url = "https://ark.cn-beijing.volces.com/api/v3"
        config = Config()

        api_key = config.get("volcengine_api_key")
        super().__init__(api_key, base_url, max_tokens=8192)
        if model is None or model == "":
            model = "deepseek-r1-250528"
        self.model = model
