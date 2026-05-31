






from core.llms._llm_api_client import LLMApiClient
from core.llms.simple_deep_seek_client import SimpleDeepSeekClient
from ..utils.config_setting import Config

class SimpleDeepSeekClientSpeciale(LLMApiClient):
    pass

class SimpleDeepSeekClientSpeciale(SimpleDeepSeekClient):
    def __init__(self, model: str = "deepseek-reasoner"):
        config = Config()
        api_key = config.get("deep_seek_api_key")
        model = "deepseek-reasoner"
        super().__init__(api_key, model=model,base_url="https://api.deepseek.com/v3.2_speciale_expires_on_20251215")