from sentence_transformers import CrossEncoder
from typing import List
from ._ranker import Ranker

class BGERerankerLarge(Ranker):
    def __init__(self,max_length:int=1024):
        from ..utils.get_sentence_device import get_sentence_transformer_device
        device = get_sentence_transformer_device()
        self.model = CrossEncoder('BAAI/bge-reranker-large',device=device,max_length=max_length)

    def get_scores(self, pairs:List[List[str]]) -> List[List[float]]:
        return self.model.predict(pairs) 