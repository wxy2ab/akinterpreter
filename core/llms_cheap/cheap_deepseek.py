from ..llms.deep_seek_client import DeepSeekClient

class CheapDeepSeek(DeepSeekClient):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.model = "deepseek-chat"