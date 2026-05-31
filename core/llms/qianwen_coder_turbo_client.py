from .qianwen_client import QianWenClient
from ..utils.config_setting import Config
from ._llm_api_client import LLMApiClient

class QianWenCoderTurboClient(LLMApiClient):
    pass

class QianWenCoderTurboClient(QianWenClient):
    def __init__(self, model: str = "qwen3-coder-480b-a35b-instruct"):
        config = Config()
        api_key = config.get("dashscope_api_key")
        if model is None or model == "":
            model = "qwen3-coder-480b-a35b-instruct"
        self.model = model
        super().__init__(api_key, max_tokens=8192 ,model=self.model)
