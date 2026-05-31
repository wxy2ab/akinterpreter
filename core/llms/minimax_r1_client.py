from core.llms.mini_max_client import MiniMaxClient

from ..utils.config_setting import Config
from ._llm_api_client import LLMApiClient

class MiniMaxR1Client(LLMApiClient):
    pass



class MiniMaxR1Client(MiniMaxClient):
    def __init__(self, model: str = "DeepSeek-R1"):
        config = Config()
        api_key = config.get("minimax_api_key")
        super().__init__(api_key, model)




