from typing import List
from abc import ABC, abstractmethod
import numpy as np
from ..embeddings.embedding_factory import EmbeddingFactory
from ..embeddings._embedding import Embedding

embedding_factory = EmbeddingFactory()
embedding_client = embedding_factory.get_instance()

def embedding_similarity(a: List[float], b: List[float]) -> float:
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

class Memory:
    def __init__(self, embedding_client: Embedding = embedding_client, sim_func=embedding_similarity):
        self.data = []
        self.embedding_client = embedding_client
        self.sim_func = sim_func

    def save_memory(self, text: str):
        embedding = self.embedding_client.convert_to_embedding([text])[0]
        self.data.append({
            "text": text,
            "emb": embedding
        })

    def retrieve(self, query: str, topk: int = 2) -> str:
        query_emb = self.embedding_client.convert_to_embedding([query])[0]
        memory = sorted(self.data, key=lambda x: self.sim_func(x['emb'], query_emb), reverse=True)[:topk]
        texts = [m['text'] for m in memory]
        texts = [''] + texts + ['']
        return '\n----\n'.join(texts)