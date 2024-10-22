import json
import numpy as np
from typing import List, Dict, Any, Union, Generator
from ..embeddings.embedding_factory import EmbeddingFactory
from ..embeddings._embedding import Embedding
from ..llms_cheap.llms_cheap_factory import LLMCheapFactory

embedding_factory = EmbeddingFactory()
embedding_client = embedding_factory.get_instance()
llm_cheap_factory = LLMCheapFactory()
llm_cheap = llm_cheap_factory.get_instance()

def embedding_similarity(a: List[float], b: List[float]) -> float:
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

class Memory:
    def __init__(self, embedding_client: Embedding = embedding_client, sim_func=embedding_similarity):
        self.data: List[Dict[str, Any]] = []
        self.embedding_client = embedding_client
        self.sim_func = sim_func
        self.llm_cheap = llm_cheap

    def save_memory(self, text: str):
        embedding = self.embedding_client.convert_to_embedding([text])[0]
        self.data.append({
            "text": text,
            "emb": embedding
        })

    def batch_save(self, texts: List[str], batch_size: int = 16):
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            embeddings = self.embedding_client.convert_to_embedding(batch)
            for text, embedding in zip(batch, embeddings):
                self.data.append({
                    "text": text,
                    "emb": embedding
                })

    def preprocess_query(self, query: str, is_stream: bool = False) -> Union[str, Generator[str, None, None]]:
        preprocess_prompt = f"""原始查询：{query}

请分析这个查询，并提供以下信息：
1. 主要查询对象：（例如：股票、指数、期货、美股、港股等）
2. 数据类型：（例如：行情数据、财务数据、研究报告等）
3. 关键词：（提取查询中的关键词，可以包括同义词）

请注意：
- 保持信息简洁，每项提供1-3个关键词。
- 不要添加原始查询中没有的额外信息或推测。
- 如果遇到具体的股票代码，请用"股票"替代。
- 如果遇到期货合约代码，请用"期货合约"代替
- 如果遇到指数代码，请用"指数"代替
- 严格区分股票、期货、指数。如非必要不要让这些词混合出现
- 时间信息，比如2024年，时间范围，比如1月到6月，是没有帮助的，不要提供。
- 具体的股票代码、合约代码、指数代码没有帮助，不要提供。
- 如果查询提及数据周期，需要添加周期关键词，比如"日线"、"分钟"等，查询数据的默认周期是日线。
- 请反复检查有没有违反上面的注意事项

请直接列出关键信息，无需包含"主要查询对象："、"数据类型："和"关键词："等标签。
每项信息占一行，用逗号分隔多个词。

例如：
股票,
行情数据,财务报表
日线,成交量,市值
"""
        if is_stream:
            return self._process_stream_result(self.llm_cheap.one_chat(preprocess_prompt, is_stream=True))
        else:
            focused_query = self.llm_cheap.one_chat(preprocess_prompt).strip()
            return self._process_result(focused_query)


    def llm_rank(self, query: str, texts: List[str], top_k: int) -> List[str]:
        # 准备用于LLM排序的提示
        numbered_functions = [f"编号:{i+1}, 函数:{text}" for i, text in enumerate(texts)]
        ranking_prompt = f"""任务：{query}

你是一个智能助手，需要帮助用户完成上述任务。以下是可能有助于完成任务的函数列表。请仔细分析每个函数，并选择最可能帮助完成任务的函数。

可用函数列表：
{chr(10).join(numbered_functions)}

评估标准：
1. 函数的功能是否直接匹配任务需求
2. 函数的输入输出是否符合任务要求
3. 函数的描述是否暗示它可以处理任务中提到的数据类型或操作

请提供您的选择结果，使用以下格式：
[最符合的编号1, 最符合的编号2, 最符合的编号3, ...]

注意事项：
- 只返回编号，不要返回函数名称。
- 最相关的函数应该排在前面。
- 只包括相关的函数，最多不超过{top_k}个。
- 如果没有相关函数，请返回空列表 []。
- 确保返回的编号在有效范围内（1到{len(texts)}）。

您的选择结果："""

        # 获取LLM的排序结果
        llm_response = self.llm_cheap.one_chat(ranking_prompt).strip()
        
        # 解析排序结果
        try:
            # 移除可能的前后缀并分割
            numbers = [int(num.strip()) for num in llm_response.strip('[]').replace(' ', '').split(',') if num.strip()]
            
            # 过滤有效的编号并转换为0-based索引
            valid_indices = [num - 1 for num in numbers if 1 <= num <= len(texts)]
            
            # 如果没有有效的排序结果，使用原始顺序
            if not valid_indices:
                print("未找到有效的排序结果。使用原始顺序。")
                valid_indices = list(range(min(top_k, len(texts))))
            else:
                # 限制结果数量
                valid_indices = valid_indices[:top_k]
        except Exception as e:
            print(f"解析LLM排序结果时出错：{e}。使用原始顺序。")
            valid_indices = list(range(min(top_k, len(texts))))

        # 返回排序后的函数
        return [texts[i] for i in valid_indices]

    def llm_rank2(self, query: str, texts: List[str], top_k: int) -> List[str]:
        # 准备用于LLM排序的提示
        ranking_prompt = f"""查询：{query}

请根据与查询的相关性对以下文本进行排序。考虑以下标准：
1. 文本对查询的回答或解决程度
2. 提供的相关信息量
3. 信息的准确性和可靠性

需要排序的文本：
{chr(10).join([f"{i+1}. {text}" for i, text in enumerate(texts)])}

请提供您的排序结果，以逗号分隔的数字列表形式表示相关性顺序，最相关的排在前面。例如：3,1,4,2,5

您的排序结果："""

        # 获取LLM的排序结果
        llm_response = self.llm_cheap.one_chat(ranking_prompt).strip()
        
        # 解析排序结果
        try:
            ranking = [int(x.strip()) for x in llm_response.split(',')]
            # 确保所有索引都是有效的
            ranking = [i for i in ranking if 1 <= i <= len(texts)]
            # 移除重复项，同时保持顺序
            ranking = list(dict.fromkeys(ranking))
        except ValueError:
            print("解析LLM排序结果时出错。回退到原始顺序。")
            ranking = list(range(1, len(texts) + 1))

        # 应用排序并返回前top_k个结果
        ranked_texts = [texts[i-1] for i in ranking[:top_k]]
        return ranked_texts

    def _process_result(self, result: str) -> str:
        lines = result.strip().split('\n')
        processed_lines = []
        for line in lines:
            if ':' in line:
                line = line.split(':', 1)[1].strip()
            processed_lines.append(line)
        return '\n'.join(processed_lines)

    def _process_stream_result(self, stream: Generator[str, None, None]) -> Generator[str, None, None]:
        buffer = ""
        for chunk in stream:
            buffer += chunk
            lines = buffer.split('\n')
            for line in lines[:-1]:
                if ':' in line:
                    line = line.split(':', 1)[1].strip()
                yield line + '\n'
            buffer = lines[-1]
        if buffer:
            if ':' in buffer:
                buffer = buffer.split(':', 1)[1].strip()
            yield buffer

    def retrieve(self, query: str, initial_topk: int = 50, final_topk: int = 5) -> str:
        reranked_texts = self.retrieves(query, initial_topk, final_topk)
        reranked_texts = [''] + reranked_texts + ['']
        return '\n----\n'.join(reranked_texts)

    def retrieves(self, query: str, initial_topk: int = 50, final_topk: int = 5) -> List[str]:
        # Preprocess the query
        focused_query = self.preprocess_query(query)
        
        # Generate embedding for the preprocessed query
        query_emb = self.embedding_client.convert_to_embedding([focused_query])[0]
        
        # Initial retrieval
        memory = sorted(self.data, key=lambda x: self.sim_func(x['emb'], query_emb), reverse=True)[:initial_topk]
        texts = [m['text'] for m in memory]
        
        # Use LLM for ranking
        ranked_texts = self.llm_rank(f"{query}", texts, final_topk)
        
        return ranked_texts
    def get_functions(self, query: str, initial_topk: int = 50, final_topk: int = 5) -> List[str]:
        """
        获取与查询最相关的函数名列表。

        Args:
            query (str): 查询字符串，描述要完成的任务。
            initial_topk (int): 初始检索的函数数量。默认为50。
            final_topk (int): 最终返回的函数数量。默认为5。

        Returns:
            List[str]: 最相关函数名的列表。
        """
        retrieved_functions = self.retrieves(query, initial_topk, final_topk)
        
        # 提取函数名
        function_names = []
        for func in retrieved_functions:
            # 假设函数描述的格式是 "函数名: 函数描述"
            parts = func.split(':', 1)
            if len(parts) > 1:
                function_names.append(parts[0].strip())
            else:
                # 如果没有冒号，就使用整个字符串作为函数名
                function_names.append(func.strip())
        
        return function_names
    def llm_rank1(self, query: str, texts: List[str], top_k: int) -> List[str]:
        # Prepare the prompt for LLM ranking
        ranking_prompt = f"""Query: {query}

Please rank the following texts based on their relevance to the query. Consider the following criteria:
1. How well the text answers or addresses the query
2. The amount of relevant information provided
3. The accuracy and reliability of the information

Texts to rank:
{chr(10).join([f"{i+1}. {text}" for i, text in enumerate(texts)])}

Provide your ranking as a comma-separated list of numbers representing the order of relevance, with the most relevant first. For example: 3,1,4,2,5

Your ranking:"""

        # Get LLM's ranking
        llm_response = self.llm_cheap.one_chat(ranking_prompt).strip()
        
        # Parse the ranking
        try:
            ranking = [int(x.strip()) for x in llm_response.split(',')]
            # Ensure all indices are valid
            ranking = [i for i in ranking if 1 <= i <= len(texts)]
            # Remove duplicates while preserving order
            ranking = list(dict.fromkeys(ranking))
        except ValueError:
            print("Error parsing LLM ranking. Falling back to original order.")
            ranking = list(range(1, len(texts) + 1))

        # Apply the ranking and return top_k results
        ranked_texts = [texts[i-1] for i in ranking[:top_k]]
        return ranked_texts
    def search_documents(self, query: str, topk: int = 50) -> List[str]:
        """
        直接搜索与查询最相关的文档，不经过rerank步骤。

        Args:
            query (str): 查询字符串。
            topk (int): 返回的文档数量。默认为50。

        Returns:
            List[str]: 最相关文档的列表。
        """
        # 预处理查询
        focused_query = self.preprocess_query(query)
        
        # 为预处理后的查询生成嵌入
        query_emb = self.embedding_client.convert_to_embedding([focused_query])[0]
        
        # 使用嵌入相似度排序并选择前topk个结果
        sorted_data = sorted(self.data, key=lambda x: self.sim_func(x['emb'], query_emb), reverse=True)
        top_results = sorted_data[:topk]
        
        # 返回文档内容
        return [item['text'] for item in top_results]
    def to_json(self) -> str:
        return json.dumps({"data": self.data}, default=lambda obj: obj.tolist() if isinstance(obj, np.ndarray) else obj)

    @classmethod
    def from_json(cls, json_str: str, embedding_client: Embedding = embedding_client, sim_func=embedding_similarity) -> 'Memory':
        memory = cls(embedding_client, sim_func)
        data = json.loads(json_str)
        memory.data = data["data"]
        return memory

    def save_to_file(self, filename: str):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({"data": self.data}, f, default=lambda obj: obj.tolist() if isinstance(obj, np.ndarray) else obj)

    @classmethod
    def load_from_file(cls, filename: str, embedding_client: Embedding = embedding_client, sim_func=embedding_similarity) -> 'Memory':
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        memory = cls(embedding_client, sim_func)
        memory.data = data["data"]
        return memory