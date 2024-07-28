
from .moonshot_client import MoonShotClient
from ..utils.config_setting import Config
from ._llm_api_client import LLMApiClient

class Zero1LLamaImproverClient(LLMApiClient):
    pass

class Zero1LLamaImproverClient(MoonShotClient):
    def __init__(self, model: str = "zero1-improver"):
        base_url = "https://api.lingyiwanwu.com/v1"
        config = Config()
        api_key = config.get("zero_one_api_key")
        super().__init__(api_key, base_url)
        self._model_list=["yi-large","yi-medium","yi-large-turbo"]
        self.model = "yi-large-turbo"

