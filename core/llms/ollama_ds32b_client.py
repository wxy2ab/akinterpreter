from .moonshot_client import MoonShotClient
from ..utils.config_setting import Config
from ._llm_api_client import LLMApiClient

class OllamaDS32bClient(LLMApiClient):
    pass



class OllamaDS32bClient(MoonShotClient):
    def __init__(self, model: str = "deepseek-r1:32b"):
        
        config = Config()

        ollama_url = config.get("ollama_url")
        base_url = ollama_url
        api_key='ollama'
        super().__init__(api_key, base_url, max_tokens=8196)
        if model is None or model == "":
            model = "deepseek-r1:32b"
        self.model = model
