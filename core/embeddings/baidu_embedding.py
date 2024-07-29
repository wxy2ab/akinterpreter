from ._embedding import Embedding
from .bge_large_zh import BGELargeZhAPI

class BadiduEmbedding(Embedding):
    pass

class BadiduEmbedding(BGELargeZhAPI):
    def __init__(self, api_key: str = "", secret_key: str = "", model_name: str = "embedding-v1"):
        super().__init__(api_key, secret_key, model_name)
    
    @property
    def vector_size(self) -> int:
        return 384