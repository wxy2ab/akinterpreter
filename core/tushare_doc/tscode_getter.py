

from qdrant_client import QdrantClient

from ..llms_cheap.llms_cheap_factory import LLMCheapFactory
from ..rag.qdrant_client_singleton import QdrantClientSingleton
from ..embeddings.embedding_factory import EmbeddingFactory
from ..embeddings._embedding import Embedding
from ..embeddings.ranker_factory import RankerFactory
from ..embeddings._ranker import Ranker



class TscodeGetter:
    def __init__(self):
        self.db_path = "./database/embedding/tushare.db"
        self.collection_name = 'ts_codes'
        # 初始化嵌入生成器
        embedding_factory = EmbeddingFactory()
        self.embedding: Embedding = embedding_factory.get_instance()

        # 初始化排序器
        ranker_factory = RankerFactory()
        self.ranker: Ranker = ranker_factory.get_instance()
        self.client: QdrantClient = QdrantClientSingleton.get_instance(self.db_path)

        # 初始化 Cheap LLM 客户端
        llm_cheap_factory = LLMCheapFactory()
        self.llm_cheap = llm_cheap_factory.get_instance()

    def get_tscode(self, value: str) -> str:
        # 生成查询的嵌入向量
        query_vector = self.embedding.convert_to_embedding([value])[0]

        # 从数据库中查询前10个最相似的结果
        search_result = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=10
        )

        # 准备 LLM 输入
        candidates = [item.payload for item in search_result]
        prompt = f"Given the query '{value}', which of the following candidates is most relevant? If none are relevant, say 'None'.\n\n"
        for i, candidate in enumerate(candidates):
            prompt += f"{i+1}. {candidate['content']}\n"

        # 使用 LLM 判断最相关的结果
        llm_response = self.llm_cheap.one_chat(prompt)

        # 解析 LLM 响应
        if "None" in llm_response:
            return ""
        else:
            # 假设 LLM 返回了最相关的候选项的编号
            most_relevant_index = int(llm_response.strip().split('.')[0]) - 1
            return candidates[most_relevant_index]['ts_code']

    def __getter__(self, value: str) -> str:
        # 生成查询的嵌入向量
        query_vector = self.embedding.convert_to_embedding([value])[0]

        # 从数据库中查询前50个最相似的结果
        search_result = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=50
        )

        # 准备 reranker 输入
        candidates = [item.payload for item in search_result]
        reranked_results = self.ranker.rank(value, candidates)

        # 获取 rerank 后的最相关结果
        top_result = reranked_results[0]

        # 使用 LLM 判断内容是否一致
        prompt = f"Are the following two pieces of text consistent in meaning? Answer only 'Yes' or 'No'.\n\nText 1: {value}\nText 2: {top_result['content']}"
        llm_response = self.llm_cheap.one_chat(prompt)

        if "yes" in llm_response.strip().lower() :
            return top_result['ts_code']
        else:
            return ""
