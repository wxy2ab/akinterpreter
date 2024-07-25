from core.llms.openai_client import OpenAIClient


class CheapOpenai(OpenAIClient):

    def __init__(self, api_key: str = ""):
        super().__init__(api_key=api_key, model="gpt-4o-mini")
