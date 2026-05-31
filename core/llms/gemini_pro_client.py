#"gemini-2.0-pro-exp-02-05"

from .gemini2_client import Gemini2Client
from ..utils.config_setting import Config
from ._llm_api_client import LLMApiClient


class GeminiProClient(LLMApiClient):
    pass

class GeminiProClient(Gemini2Client):
    def __init__(self, model: str = "gemini-2.0-pro-exp-02-05"):
        config = Config()
        api_key = config.get("google_api_key")  
        if model is None or model == "":
            model = "gemini-2.0-pro-exp-02-05"
        self.model = model
        super().__init__(api_key, model=self.model)