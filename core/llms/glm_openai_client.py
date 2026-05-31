from .moonshot_client import MoonShotClient
from ..utils.config_setting import Config
from ._llm_api_client import LLMApiClient


class GLMOpenAIClient(LLMApiClient):
    pass


class GLMOpenAIClient(MoonShotClient):
    def __init__(self, model: str = "glm-5.1"):
        base_url = "https://open.bigmodel.cn/api/coding/paas/v4"
        config = Config()

        api_key = config.get("glm_api_key")
        super().__init__(api_key, base_url)
        if model is None or model == "":
            model = "glm-5.1"
        self.model = model
