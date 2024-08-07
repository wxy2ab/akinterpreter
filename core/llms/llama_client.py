from typing import Literal
from .openai_client import OpenAIClient
from ._llm_api_client import LLMApiClient
from ..utils.config_setting import Config
from ..utils.handle_max_tokens import handle_max_tokens

class LlamaClient(LLMApiClient):
    pass

class LlamaClient(OpenAIClient):
    def __init__(self, model:Literal["mixtral-8x22b-instruct","gemma2-27b","llama3.1-8b","llama3.1-70b","llama3.1-405b"] ="llama3.1-70b" , **kwargs):
        config = Config()
        api_key = config.get('llama_api_key')
        super().__init__(api_key = api_key, model=model, base_url='https://api.llama-api.com', max_tokens=4000, **kwargs)