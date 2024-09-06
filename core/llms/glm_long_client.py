from typing import Literal
from .glm_client import GLMClient
from ._llm_api_client import LLMApiClient


class GLMFreeClient(LLMApiClient):
    pass

class GLMLongClient(GLMClient):
    def __init__(self, api_key: str = "", model: Literal["glm-4-0520", "glm-4", "glm-4-air", "glm-4-airx", "glm-4-flash","glm-4-long"] = "glm-4-long",*args, **kwargs):
        super().__init__(*args, **kwargs)