from sentence_transformers import SentenceTransformer
from typing import List
from ._embedding import Embedding

class BGEM3Embedding(Embedding):
    def __init__(self):
        from ..utils.get_sentence_device import get_sentence_transformer_device
        device = get_sentence_transformer_device()
        from ..utils.config_setting import Config
        api_key = ""
        config = Config()
        if config.has_key("hugging_face_api_key"):
            api_key = config.get("hugging_face_api_key")
        # 设置 API Key
        if api_key:
            import os
            os.environ['HUGGING_FACE_HUB_TOKEN'] = api_key
        self.model = SentenceTransformer('BAAI/bge-m3',device=device,token=api_key)

    def convert_to_embedding(self, input_strings: List[str]) -> List[List[float]]:
        return self.model.encode(input_strings).tolist()

    @property
    def vector_size(self) -> int:
        return self.model.get_sentence_embedding_dimension()