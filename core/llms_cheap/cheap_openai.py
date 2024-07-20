from core.llms.openai_client import OpenAIClient


class CheapDoubao(OpenAIClient):
    def __init__(self, **kwargs):
        super().__init__(self, model="gpt-4o-mini",**kwargs)