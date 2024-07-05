from sentence_transformers import SentenceTransformer
from typing import List
from ._embedding import Embedding

class BGELargeEmbedding(Embedding):
    def __init__(self):
        self.model = SentenceTransformer('BAAI/bge-base-zh-v1.5')

    def convert_to_embedding(self, input_strings: List[str]) -> List[List[float]]:
        return self.model.encode(input_strings).tolist()