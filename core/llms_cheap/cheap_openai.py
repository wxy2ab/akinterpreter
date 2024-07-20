from core.llms.openai_client import OpenAIClient


class CheapOpenai(OpenAIClient):

    def __init__(self,api_kek:str=""):
        super().__init__(self,api_key=api_kek model="gpt-4o-mini")
