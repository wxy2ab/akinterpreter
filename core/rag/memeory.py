import json
import numpy as np
from typing import List, Dict, Any
from ..embeddings.embedding_factory import EmbeddingFactory
from ..embeddings._embedding import Embedding
from ..embeddings._ranker import Ranker
from ..embeddings.ranker_factory import RankerFactory

embedding_factory = EmbeddingFactory()
embedding_client = embedding_factory.get_instance()
reranker_factory = RankerFactory()
reranker = reranker_factory.get_instance()

def embedding_similarity(a: List[float], b: List[float]) -> float:
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

class Memory:
    def __init__(self, embedding_client: Embedding = embedding_client, sim_func=embedding_similarity, reranker: Ranker = reranker):
        self.data: List[Dict[str, Any]] = []
        self.embedding_client = embedding_client
        self.sim_func = sim_func
        self.reranker = reranker

    def save_memory(self, text: str):
        embedding = self.embedding_client.convert_to_embedding([text])[0]
        self.data.append({
            "text": text,
            "emb": embedding.tolist()
        })

    def batch_save(self, texts: List[str], batch_size: int = 16):
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            embeddings = self.embedding_client.convert_to_embedding(batch)
            for text, embedding in zip(batch, embeddings):
                self.data.append({
                    "text": text,
                    "emb": embedding.tolist()
                })

    def retrieve(self, query: str, initial_topk: int = 50, final_topk: int = 5) -> str:
        reranked_texts = self.retrieves(query, initial_topk, final_topk)
        reranked_texts = [''] + reranked_texts + ['']
        return '\n----\n'.join(reranked_texts)

    def retrieves(self, query: str, initial_topk: int = 50, final_topk: int = 5) -> List[str]:
        query_emb = self.embedding_client.convert_to_embedding([query])[0]
        
        # 初始召回
        memory = sorted(self.data, key=lambda x: self.sim_func(np.array(x['emb']), query_emb), reverse=True)[:initial_topk]
        texts = [m['text'] for m in memory]
        
        # Rerank
        rerank_pairs = [[query, text] for text in texts]
        rerank_scores = self.reranker.get_scores(rerank_pairs)
        
        # 按rerank分数排序并选择前final_topk个结果
        reranked_memory = sorted(zip(texts, rerank_scores), key=lambda x: x[1], reverse=True)[:final_topk]
        reranked_texts = [m[0] for m in reranked_memory]
        
        return reranked_texts

    def to_json(self) -> str:
        return json.dumps({"data": self.data})

    @classmethod
    def from_json(cls, json_str: str, embedding_client: Embedding = embedding_client, sim_func=embedding_similarity, reranker: Ranker = reranker) -> 'Memory':
        memory = cls(embedding_client, sim_func, reranker)
        data = json.loads(json_str)
        memory.data = data["data"]
        return memory

    def save_to_file(self, filename: str):
        with open(filename, 'w') as f:
            json.dump({"data": self.data}, f)

    @classmethod
    def load_from_file(cls, filename: str, embedding_client: Embedding = embedding_client, sim_func=embedding_similarity, reranker: Ranker = reranker) -> 'Memory':
        with open(filename, 'r') as f:
            data = json.load(f)
        memory = cls(embedding_client, sim_func, reranker)
        memory.data = data["data"]
        return memory