from typing import List, Dict, Any, Union
from core.llms.llm_factory import LLMFactory
from core.llms._llm_api_client import LLMApiClient
from core.embeddings.embedding_factory import EmbeddingFactory
from core.embeddings._embedding import Embedding
from core.embeddings.ranker_factory import RankerFactory
from core.embeddings._ranker import Ranker
from qdrant_client import QdrantClient

class AkshareFunBot:
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
        # 打印集合信息
        collection_info = self.client.get_collection('akshare_embeddings')
        print(f"Collection vector configuration: {collection_info.config.params.vectors}")

    def chat(self, message: str, is_stream: bool = False) -> Union[str, List[str]]:
        """
        使用 LLM API 处理聊天消息。

        Args:
            message (str): 用户消息。
            is_stream (bool): 是否使用流式响应。

        Returns:
            Union[str, List[str]]: LLM 的响应。
        """
        response = self.llm_api.text_chat(message, is_stream=is_stream)
        return response

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
        return ranked_documents

    def reranker_chat(self, message: str) -> Union[str, List[str]]:
        try:
            query_embedding = self.get_embeddings([message])[0]
            
            print(f"Type of query_embedding: {type(query_embedding)}")
            print(f"Length of query_embedding: {len(query_embedding)}")
            print(f"First few elements of query_embedding: {query_embedding[:5]}")

            search_result = self.client.search(
                collection_name='akshare_embeddings',
                query_vector=query_embedding,  # 直接使用查询向量
                limit=10,
                with_payload=True,
                with_vectors=False,
                search_params={"exact": False}
            )
            
            print(f"Search result: {search_result}")
            
            if search_result:
                documents = [hit.payload['content'] for hit in search_result]
                names = [hit.payload['name'] for hit in search_result]
            else:
                print("No search results found")
                return []

            # 对文档进行排序
            ranked_documents = self.rank_documents(message, documents)

            # 提取前 5 个文档的 name
            top_names = [names[documents.index(doc['document'])] for doc in ranked_documents[:5]]

            return top_names
        except Exception as e:
            print(f"An error occurred: {e}")
            return []

# 示例使用
if __name__ == "__main__":
    bot = AkshareFunBot()
    user_message = "请告诉我关于 Akshare 的信息。"
    
    # 进行 reranker chat
    response = bot.reranker_chat(user_message)
    print("Reranker Chat Response:", response)
