from .qianwen_client import QianWenClient
from ..utils.config_setting import Config
from ._llm_api_client import LLMApiClient

class AliDeepSeekClient(LLMApiClient):
    pass

class AliDeepSeekClient(QianWenClient):
    def __init__(self, model: str = "deepseek-v3"):
        config = Config()
        api_key = config.get("dashscope_api_key")
        if model is None or model == "":
            model = "deepseek-v3"
        self.model = model
        super().__init__(api_key, max_tokens=8192 ,model=self.model)

