from .moonshot_client import MoonShotClient
from ..utils.config_setting import Config
from ._llm_api_client import LLMApiClient

class VolcDeepSeekClient(LLMApiClient):
    pass



class VolcDeepSeekClient(MoonShotClient):
    def __init__(self, model: str = "deepseek-v3-250324"):
        base_url = "https://ark.cn-beijing.volces.com/api/v3"
        config = Config()

        api_key = config.get("volcengine_api_key")
        super().__init__(api_key, base_url, max_tokens=8192)
        if model is None or model == "":
            model = "deepseek-v3-250324"
        self.model = model
