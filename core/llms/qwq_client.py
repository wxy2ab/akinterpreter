from .moonshot_client import MoonShotClient
from ..utils.config_setting import Config
from ._llm_api_client import LLMApiClient

class QwqClient(LLMApiClient):
    pass


class QwqClient(MoonShotClient):
    def __init__(self, model: str = "free:QwQ-32B"):
        base_url = "https://api.siliconflow.cn/v1"
        config = Config()

        api_key = "sk-W0rpStc95T7JVYVwDYc29IyirjtpPPby6SozFMQr17m8KWeo"
        super().__init__(api_key, base_url, max_tokens=4096)
        if model is None or model == "":
            model = "free:QwQ-32B"
        self.model = model
