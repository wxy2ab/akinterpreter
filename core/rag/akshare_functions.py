import re
from typing import Generator, List, Dict, Any, Union
from ..llms.llm_factory import LLMFactory
from ..llms._llm_api_client import LLMApiClient
from ..embeddings.embedding_factory import EmbeddingFactory
from ..embeddings._embedding import Embedding
from ..embeddings.ranker_factory import RankerFactory
from ..embeddings._ranker import Ranker
from ..llms_cheap.llms_cheap_factory import LLMCheapFactory
from .qdrant_client_singleton import QdrantClientSingleton
from .build_embedding_db import build_akshare_embedding_db
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
            build_akshare_embedding_db()

        #初始化 Qdrant 客户端
        self.client = QdrantClientSingleton.get_instance(db_path)

        #初始化 Cheap LLM 客户端
        llm_cheap_factory = LLMCheapFactory()
        self.llm_cheap = llm_cheap_factory.get_instance()

        # 设置集合名称
        self.collection_name = 'akshare_embeddings'

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

    def preprocess_query(self, query: str, is_stream: bool = False) -> Union[str, Generator[str, None, None]]:
        """
        使用 LLM 对查询进行预处理和聚焦。

        Args:
            query (str): 原始查询语句。
            is_stream (bool): 是否使用流式调用，默认为 False。

        Returns:
            Union[str, Generator[str, None, None]]: 预处理后的查询语句，或生成器（如果 is_stream 为 True）。
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
- 时间信息，比如2024年，时间范围，比如1月到6月，是没有帮助的，不要提供。
- 如果查询提及数据周期，需要添加周期关键词，比如"日线"、"分钟"等。

请直接列出关键信息，无需包含"主要查询对象："、"数据类型："和"关键词："等标签。
每项信息占一行，用逗号分隔多个词。

例如：
股票,指数
行情数据,财务报表
日K线,成交量,市值
"""
        if is_stream:
            return self._process_stream_result(self.llm_cheap.one_chat(preprocess_prompt, is_stream=True))
        else:
            focused_query = self.llm_cheap.one_chat(preprocess_prompt).strip()
            return self._process_result(focused_query)

    def _process_result(self, result: str) -> str:
        """处理非流式结果"""
        lines = result.strip().split('\n')
        processed_lines = []
        for line in lines:
            # 移除可能的标签
            if ':' in line:
                line = line.split(':', 1)[1].strip()
            processed_lines.append(line)
        return '\n'.join(processed_lines)

    def _process_stream_result(self, stream: Generator[str, None, None]) -> Generator[str, None, None]:
        """处理流式结果"""
        buffer = ""
        for chunk in stream:
            buffer += chunk
            lines = buffer.split('\n')
            for line in lines[:-1]:
                # 移除可能的标签
                if ':' in line:
                    line = line.split(':', 1)[1].strip()
                yield line + '\n'
            buffer = lines[-1]
        if buffer:
            if ':' in buffer:
                buffer = buffer.split(':', 1)[1].strip()
            yield buffer

    def get_functions(self, query: str, n: int = 5, is_stream: bool = False) -> Union[List[str], Generator[List[str], None, None]]:
        """
        获取经过 llm_cheap reranker 排序后前 n 个最相关的函数名。

        Args:
            query (str): 查询语句。
            n (int): 返回的函数数量，默认为5。
            is_stream (bool): 是否使用流式调用，默认为 False。

        Returns:
            Union[List[str], Generator[List[str], None, None]]: 函数名列表或生成器（如果 is_stream 为 True）。
        """
        try:
            # 预处理查询
            focused_query = self.preprocess_query(query)
            print(f"聚焦后的查询:\n{focused_query}")

            # 从预处理后的消息生成嵌入
            query_embedding = self.get_embeddings([focused_query])[0]

            # 从数据库中检索文档
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=max(50, n),
                with_payload=True
            )

            if not search_result:
                print("未找到搜索结果")
                return [] if not is_stream else ([] for _ in range(1))

            documents = [hit.payload['content'] for hit in search_result]
            names = [hit.payload['name'] for hit in search_result]

            # 使用 llm_cheap 进行重新排序
            rerank_prompt = f"""原始查询：{query}

请根据以下查询信息，从给定的函数列表中选择最相关的函数。评估时请考虑：
1. 函数是否能处理查询所需的数据类型和对象
2. 函数名称是否与查询的关键概念匹配
3. 函数的描述是否与查询的需求相符

返回前{n}个最相关函数的名称，每行一个。
请务必仅返回函数名，不要包含任何其他文字说明或编号。

函数列表：
"""
            for doc in documents:
                rerank_prompt += f"{doc}\n"

            if is_stream:
                return self._process_stream_functions(self.llm_cheap.one_chat(rerank_prompt, is_stream=True), names, n)
            else:
                rerank_result = self.llm_cheap.one_chat(rerank_prompt)
                return self._process_functions(rerank_result, names, n)

        except Exception as e:
            print(f"发生错误：{e}")
            return [] if not is_stream else ([] for _ in range(1))

    def _process_stream_functions(self, stream: Generator[str, None, None], names: List[str], n: int) -> Generator[List[str], None, None]:
        """
        处理流式输出的函数名，只保留最终的函数列表。

        Args:
            stream (Generator[str, None, None]): 输入的字符流。
            names (List[str]): 有效的函数名列表。
            n (int): 需要返回的函数数量。

        Yields:
            List[str]: 最终的函数名列表。
        """
        full_text = ""
        for chunk in stream:
            full_text += chunk
        
        # 处理完整的文本
        lines = full_text.split('\n')
        top_names = []
        for line in lines:
            name = line.strip()
            if name in names and name not in top_names:
                top_names.append(name)
                if len(top_names) == n:
                    yield top_names
                    return

        # 如果流结束时仍未达到 n 个函数，用原始顺序补充
        if len(top_names) < n:
            remaining_names = [name for name in names if name not in top_names]
            top_names.extend(remaining_names[:n-len(top_names)])

        yield top_names

    def _process_functions(self, result: str, names: List[str], n: int) -> List[str]:
        """
        处理非流式输出的函数名。

        Args:
            result (str): 完整的输出结果。
            names (List[str]): 有效的函数名列表。
            n (int): 需要返回的函数数量。

        Returns:
            List[str]: 处理后的函数名列表。
        """
        result_lines = result.strip().split('\n')
        top_names = [line.strip() for line in result_lines if line.strip() in names][:n]
        if len(top_names) < n:
            remaining_names = [name for name in names if name not in top_names]
            top_names.extend(remaining_names[:n-len(top_names)])
        return top_names

    def search_documents(self,query:str,n:int=50)->list[str]:
        """
        使用 QdrantDB 搜索文档。

        Args:
            query (str): 查询语句。
            n (int): 返回的文档数量，默认为50。

        Returns:
            list[str]: 包含搜索结果的文档列表。
        """
        # 从数据库中检索文档
        search_result = self.client.search(
            collection_name=self.collection_name,
            query_vector=self.get_embeddings([query])[0],
            limit=n,
            with_payload=True
        )

        if not search_result:
            print("未找到搜索结果")
            return []

        documents = [hit.payload['content'] for hit in search_result]
        return documents
# 示例使用
if __name__ == "__main__":
    functions = AkshareFunctions()
    query = "获取股票数据的方法"
    
    # 获取前 5 个函数的名称
    top_functions = functions.get_functions(query)
    print("Top 5 Functions:", top_functions)