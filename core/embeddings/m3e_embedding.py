from sentence_transformers import SentenceTransformer
from typing import List
from ._embedding import Embedding

class M3EEmbedding(Embedding):
    def __init__(self):
        self.model = SentenceTransformer('moka-ai/m3e-base')

    def convert_to_embedding(self, input_strings: List[str]) -> List[List[float]]:
        return self.model.encode(input_strings).tolist()