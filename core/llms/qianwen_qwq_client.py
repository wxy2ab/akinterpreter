from .qianwen_client import QianWenClient
from ..utils.config_setting import Config
from ._llm_api_client import LLMApiClient

class QianWenQwqClient(LLMApiClient):
    pass

class QianWenQwqClient(QianWenClient):
    def __init__(self, model: str = "qwq-32b-preview"):
        config = Config()
        api_key = config.get("dashscope_api_key")
        if model is None or model == "":
            model = "qwq-32b-preview"
        self.model = model
        super().__init__(api_key, max_tokens=8192 ,model=self.model)
