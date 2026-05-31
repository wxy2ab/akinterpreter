from .moonshot_client import MoonShotClient
from ..utils.config_setting import Config
from ._llm_api_client import LLMApiClient

class QianWenPlusClient(LLMApiClient):
    pass

class QianWenPlusClient(MoonShotClient):
    def __init__(self, model: str = "qwen3.6-plus"):
        base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        config = Config()
        api_key = config.get("dashscope_api_key") or ""
        super().__init__(api_key, base_url, max_tokens=65535)
        if model is None or model == "":
            model = "qwen3.6-plus"
        self.model = model
        
