from typing import Literal
from .openai_client import OpenAIClient
from ._llm_api_client import LLMApiClient
from ..utils.config_setting import Config
from ..utils.handle_max_tokens import handle_max_tokens

class SparkClient(LLMApiClient):
    pass

class SparkClient(OpenAIClient):
    def __init__(self, model:Literal["general","generalv3","pro-128k","generalv3.5","4.0Ultra"] ="4.0Ultra" , **kwargs):
        config = Config()
        api_key = config.get('xunfei_spark_api_key')
        secret_key = config.get('xunfei_spark_secret_key')
        api_key=f"{api_key}:{secret_key}"
        super().__init__(api_key = api_key, model=model, base_url='https://spark-api-open.xf-yun.com/v1', max_tokens=8000, **kwargs)