from .qianwen_client import QianWenClient
from ..utils.config_setting import Config
from ._llm_api_client import LLMApiClient

class QianWenCoder14Client(LLMApiClient):
    pass

class QianWenCoder14Client(QianWenClient):
    def __init__(self, model: str = "qwen3-14b"):
        config = Config()
        api_key = config.get("dashscope_api_key")
        if model is None or model == "":
            model = "qwen3-14bt"
        self.model = model
        super().__init__(api_key, max_tokens=8192 ,model=self.model)
