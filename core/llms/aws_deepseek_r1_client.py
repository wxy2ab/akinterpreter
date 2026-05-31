from .moonshot_client import MoonShotClient
from ..utils.config_setting import Config
from ._llm_api_client import LLMApiClient

class AWSDeepSeekR1Client(LLMApiClient):
    pass


class AWSDeepSeekR1Client(MoonShotClient):
    def __init__(self, model: str = "Pro/deepseek-ai/DeepSeek-R1"):
        base_url = "https://api.siliconflow.cn/v1"
        config = Config()


        api_key = config.get("aws_sf_key")
        super().__init__(api_key, base_url, max_tokens=8192)
        if model is None or model == "":
            model = "deepseek-ai/DeepSeek-R1"
        self.model = model
