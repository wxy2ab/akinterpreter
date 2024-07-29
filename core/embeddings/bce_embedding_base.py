from sentence_transformers import SentenceTransformer
from typing import List
from ._embedding import Embedding
from BCEmbedding import EmbeddingModel
from ..utils.config_setting import Config
#bce-reranker-base_v1

class BCEBaseEmbedding(Embedding):
    def __init__(self):
        from ..utils.get_sentence_device import get_sentence_transformer_device
        config = Config()
        api_key = config.get("hugging_face_api_key")
        device = get_sentence_transformer_device()
        self.model = EmbeddingModel(model_name_or_path="maidalun1020/bce-embedding-base_v1",token=api_key)

    def convert_to_embedding(self, input_strings: List[str]) -> List[List[float]]:
        return self.model.encode(input_strings).tolist()
    
    def get_scores(self, pairs: List[List[str]]) -> List[float]:
        return self.model.predict(pairs)
    
    @property
    def vector_size(self) -> int:
        return 768