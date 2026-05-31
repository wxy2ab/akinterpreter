from core.llms.mini_max_client import MiniMaxClient

from ..utils.config_setting import Config
from ._llm_api_client import LLMApiClient

class MiniMaxTextClient(LLMApiClient):
    pass



class MiniMaxTextClient(MiniMaxClient):
    def __init__(self, model: str = "MiniMax-M2"):
        config = Config()
        api_key = config.get("MiniMax-M2")
        super().__init__(api_key, model)




