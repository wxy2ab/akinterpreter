from .bge_large_zh import BGELargeZhAPI

class BadiduEmbedding(BGELargeZhAPI):
    def __init__(self, api_key: str = "", secret_key: str = "", model_name: str = "embedding-v1"):
        super().__init__(api_key, secret_key, model_name)