from typing import List, Dict, Any
from core.llms.llm_factory import LLMFactory
from core.llms._llm_api_client import LLMApiClient
from core.embeddings.embedding_factory import EmbeddingFactory
from core.embeddings._embedding import Embedding
from core.embeddings.ranker_factory import RankerFactory
from core.embeddings._ranker import Ranker
from qdrant_client import QdrantClient

class AkshareFunctions:
    def __init__(self):
        # 初始化 LLM API 客户端
        factory = LLMFactory()
        self.llm_api: LLMApiClient = factory.get_instance()

        # 初始化嵌入生成器
        embedding_factory = EmbeddingFactory()
        self.embedding: Embedding = embedding_factory.get_instance()

        # 初始化排序器
        ranker_factory = RankerFactory()
        self.ranker: Ranker = ranker_factory.get_instance()

        # 连接到 QdrantDB
        db_path = './database/embedding/akshare.db'
        self.client = QdrantClient(path=db_path)

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        将文本转换为嵌入。

        Args:
            texts (List[str]): 要转换的文本列表。

        Returns:
            List[List[float]]: 文本的嵌入表示。
        """
        embeddings = self.embedding.convert_to_embedding(texts)
        return embeddings

    def rank_documents(self, query: str, documents: List[str]) -> List[Dict[str, Any]]:
        """
        对文档进行排序。

        Args:
            query (str): 查询语句。
            documents (List[str]): 要排序的文档列表。

        Returns:
            List[Dict[str, Any]]: 包含文档及其评分的列表。
        """
        scores = self.ranker.rank(query, documents)
        ranked_documents = [{"document": doc, "score": score} for doc, score in zip(documents, scores)]
        return sorted(ranked_documents, key=lambda x: x["score"], reverse=True)

    def get_functions(self, query: str) -> List[str]:
        """
        获取经过 reranker 排序后前 5 个文档的 name 数组。

        Args:
            query (str): 查询语句。

        Returns:
            List[str]: 前 5 个文档的 name 数组。
        """
        try:
            # 从消息生成嵌入
            query_embedding = self.get_embeddings([query])[0]

            # 从数据库中检索文档
            search_result = self.client.search(
                collection_name='akshare_embeddings',
                query_vector=query_embedding,  # 直接使用查询向量，不需要包装在字典中
                limit=10,
                with_payload=True
            )

            if not search_result:
                print("No search results found")
                return []

            documents = [hit.payload['content'] for hit in search_result]
            names = [hit.payload['name'] for hit in search_result]

            # 对文档进行排序
            ranked_documents = self.rank_documents(query, documents)

            # 提取前 5 个文档的 name
            top_names = [names[documents.index(doc['document'])] for doc in ranked_documents[:5]]

            return top_names
        except Exception as e:
            print(f"An error occurred: {e}")
            return []

# 示例使用
if __name__ == "__main__":
    functions = AkshareFunctions()
    query = "获取股票数据的方法"
    
    # 获取前 5 个函数的名称
    top_functions = functions.get_functions(query)
    print("Top 5 Functions:", top_functions)