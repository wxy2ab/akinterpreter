import re
from typing import List, Dict, Any
from core.llms.llm_factory import LLMFactory
from core.llms._llm_api_client import LLMApiClient
from core.embeddings.embedding_factory import EmbeddingFactory
from core.embeddings._embedding import Embedding
from core.embeddings.ranker_factory import RankerFactory
from core.embeddings._ranker import Ranker
from qdrant_client import QdrantClient
from core.llms_cheap.llms_cheap_factory import LLMCheapFactory
from .build_embedding_db import build_embedding_db
import os

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
        
        #检查数据库是否存在，不存在创建数据库
        if not os.path.exists(db_path):
            build_embedding_db()

        #初始化 Qdrant 客户端
        self.client = QdrantClient(path=db_path)

        #初始化 Cheap LLM 客户端
        llm_cheap_factory = LLMCheapFactory()
        self.llm_cheap = llm_cheap_factory.get_instance()

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

    def preprocess_query(self, query: str) -> str:
        """
        使用 LLM 对查询进行预处理和聚焦。

        Args:
            query (str): 原始查询语句。

        Returns:
            str: 预处理后的查询语句。
        """
        preprocess_prompt = f"""原始查询：{query}

请分析这个查询，并提供以下信息：
1. 主要查询对象：（例如：股票、指数、期货等）
2. 数据类型：（例如：行情数据、财务数据、研究报告等）
3. 关键词：（提取查询中的关键词，可以包括同义词）

请注意：
- 保持信息简洁，每项提供1-3个关键词。
- 不要添加原始查询中没有的额外信息或推测。
- 如果遇到具体的股票代码，请用"个股"替代。
- 不要包含具体的时间范围。

请按以下格式提供信息：
主要查询对象：[填写]
数据类型：[填写]
关键词：[填写]
"""
        focused_query = self.llm_cheap.one_chat(preprocess_prompt).strip()
        
        # 额外处理：将可能遗漏的股票代码替换为"个股"
        lines = focused_query.split('\n')
        for i, line in enumerate(lines):
            if line.startswith("关键词："):
                keywords = line.split('：')[1]
                # 使用正则表达式替换股票代码
                keywords = re.sub(r'\b\d{6}\b', '个股', keywords)
                lines[i] = f"关键词：{keywords}"
        
        return '\n'.join(lines)

    def get_functions(self, query: str, n: int = 5) -> List[str]:
        """
        获取经过 llm_cheap reranker 排序后前 n 个最相关的函数名。

        Args:
            query (str): 查询语句。
            n (int): 返回的函数数量，默认为5。

        Returns:
            List[str]: 前 n 个最相关的函数名列表。
        """
        try:
            # 预处理查询
            focused_query = self.preprocess_query(query)
            print(f"聚焦后的查询:\n{focused_query}")

            # 从预处理后的消息生成嵌入
            query_embedding = self.get_embeddings([focused_query])[0]

            # 从数据库中检索文档
            search_result = self.client.search(
                collection_name='akshare_embeddings',
                query_vector=query_embedding,
                limit=max(30, n),  # 确保检索足够的候选函数
                with_payload=True
            )

            if not search_result:
                print("未找到搜索结果")
                return []

            documents = [hit.payload['content'] for hit in search_result]
            names = [hit.payload['name'] for hit in search_result]

            # 使用 llm_cheap 进行重新排序
            rerank_prompt = f"""原始查询：{query}
聚焦后的查询：
{focused_query}

请根据以上查询信息，从下面的函数列表中选择最相关的函数。评估时请考虑：
1. 函数是否处理查询所需的主要数据类型
2. 函数是否与提供的关键词相匹配
3. 函数是否适用于查询的主要对象

返回前{n}个最相关函数的名称，每行一个。
请务必仅返回函数名，不要包含任何其他文字说明或编号。
例如：
stock_zh_a_hist
stock_zh_index_daily
stock_zh_a_minute

函数列表：
"""
            for name, doc in zip(names, documents):
                rerank_prompt += f"{name}: {doc}\n"

            rerank_result = self.llm_cheap.one_chat(rerank_prompt)
            
            # 处理返回结果
            result_lines = rerank_result.strip().split('\n')
            top_names = [line.strip() for line in result_lines if line.strip() in names][:n]

            # 如果返回的函数名少于n个，用原始顺序补充
            if len(top_names) < n:
                remaining_names = [name for name in names if name not in top_names]
                top_names.extend(remaining_names[:n-len(top_names)])

            return top_names
        except Exception as e:
            print(f"发生错误：{e}")
            return []



# 示例使用
if __name__ == "__main__":
    functions = AkshareFunctions()
    query = "获取股票数据的方法"
    
    # 获取前 5 个函数的名称
    top_functions = functions.get_functions(query)
    print("Top 5 Functions:", top_functions)