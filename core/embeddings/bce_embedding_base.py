from sentence_transformers import SentenceTransformer
from typing import List
from ._embedding import Embedding

class BCEBaseEmbedding(Embedding):
    def __init__(self):
        from ..utils.get_sentence_device import get_sentence_transformer_device
        device = get_sentence_transformer_device()
        self.model = SentenceTransformer('maidalun1020/bce-embedding-base_v1',device=device)

    def get_scores(self, pairs: List[List[str]]) -> List[float]:
        return self.model.predict(pairs)
