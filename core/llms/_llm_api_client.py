from abc import ABC, abstractmethod
import re
from typing import Generator, Iterator, List, Dict, Any, Union
import pandas as pd
import numpy as np
import json
from ..utils.log import logger

class LLMApiClient(ABC):
    """LLM API客户端（如Gemini）的抽象基类。"""
    @abstractmethod
    def one_chat(self, message: Union[str, List[Union[str, Any]]], is_stream: bool = False) -> Union[str, Iterator[str]]:
        """执行单次聊天交互，不使用或存储聊天历史记录。"""
        pass
    
    @abstractmethod
    def text_chat(self, message: str, is_stream: bool = False) -> Union[str, Iterator[str]]:
        """处理文本消息并返回LLM的文本响应。"""
        pass

    @abstractmethod
    def tool_chat(self, user_message: str, tools: List[Dict[str, Any]], function_module: Any, is_stream: bool = False) -> Union[str, Iterator[str]]:
        """
        处理可以访问外部工具的文本消息。这个方法需要保存和支持聊天历史。

        - `tools`：工具规范列表（字典）。
        - `function_module`：包含要调用的工具函数的模块。

        tool_chat的实现流程：
        1. 将用户消息，tools 发送给API
        2. 接收响应，处理里面的工具调用
        3. 用function_module调配合解析出的函数名和参数用工具函数
        4. 把结果返回给API
        5. 获得并返回最终响应
        """
        pass

    @abstractmethod
    def audio_chat(self, message: str, audio_path: str) -> str:
        """处理文本消息和音频文件，并返回LLM的文本响应。"""
        pass

    @abstractmethod
    def video_chat(self, message: str, video_path: str) -> str:
        """处理文本消息和视频文件，并返回LLM的文本响应。"""
        pass

    @abstractmethod
    def clear_chat(self):
        """清除聊天历史或上下文。"""
        pass

    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """返回使用情况统计信息（例如，token使用情况、API调用计数）。"""
        pass
    
    def set_parameters(self, **kwargs):
        valid_params = ["temperature", "top_p", "frequency_penalty", "presence_penalty",
                        "max_tokens", "stop", "model", "stop_sequences", "logit_bias",
                        "logprobs", "top_logprobs", "penalty_score", "max_output_tokens", "do_sample", "enable_search"]
        for key, value in kwargs.items():
            if key in valid_params:
                self.parameters[key] = value
            else:
                print(f"警告：{key} 不是有效参数，将被忽略。")

    def predict_with_news(self, 
                          stock_prices: Union[List[float], pd.Series, pd.DataFrame],
                          news_data: List[Dict[str, str]],
                          num_of_predict: int,
                          stock_symbol: str = "",
                          interval: str = "天",
                          **kwargs) -> Union[List[Dict[str, float]], pd.Series, pd.DataFrame]:
        """
        使用历史价格数据和相关新闻预测未来股票价格，支持多列数据如 candlestick 数据。

        参数：
        stock_prices (Union[List[float], pd.Series, pd.DataFrame]): 历史股票价格数据。
        news_data (List[Dict[str, str]]): 包含新闻数据的字典列表。
                                          每个字典应有'date'和'headline'键。
        num_of_predict (int): 要预测的未来数据点数量。
        stock_symbol (str, 可选): 股票代码或公司名称，用于上下文。
        interval (str, 可选): 数据间隔，可选值为 "分钟"、"小时"、"天"、"周"、"月"。默认为 "天"。
        **kwargs: 传递给one_chat方法的额外关键字参数。

        返回：
        Union[List[Dict[str, float]], pd.Series, pd.DataFrame]: 与输入格式相同的预测股票价格。
        """
        # 验证interval参数
        valid_intervals = ["分钟", "小时", "天", "周", "月"]
        if interval not in valid_intervals:
            raise ValueError(f"无效的间隔值。请使用以下之一: {', '.join(valid_intervals)}")

        # 处理输入数据
        if isinstance(stock_prices, pd.DataFrame):
            price_data = stock_prices.to_json(orient='split', date_format='iso')
            columns = stock_prices.columns.tolist()
        elif isinstance(stock_prices, pd.Series):
            price_data = stock_prices.to_json(orient='split', date_format='iso')
            columns = [stock_prices.name] if stock_prices.name else ['price']
        else:
            price_data = json.dumps(stock_prices)
            columns = ['price']

        # 准备新闻数据
        formatted_news = [f"{news['date']}: {news['headline']}" for news in news_data]
        news_str = "\n".join(formatted_news[-5:])  # 仅使用最近的5条新闻

        # 构造提示词
        prompt = f"""给定以下关于{stock_symbol if stock_symbol else '某股票'}的数据：

    历史股票数据（间隔：{interval}）：
    {price_data}

    数据包含以下列：{', '.join(columns)}

    近期相关新闻：
    {news_str}

    基于这些信息，请预测未来 {num_of_predict} 个{interval}的股票数据。
    对于每个预测的时间点，请提供所有列的预测值。
    请以JSON数组的形式提供您的答案，每个元素应该是一个包含所有列的对象。
    不要包含任何额外的解释。

    例如，如果数据包含 'open', 'close', 'high', 'low', 'volume' 列，您的回答应该类似于：
    [
        {{"open": 100.5, "close": 101.2, "high": 102.0, "low": 99.8, "volume": 1000000}},
        {{"open": 101.3, "close": 102.1, "high": 102.8, "low": 100.9, "volume": 1100000}},
        ...
    ]
    """

        # 调用one_chat方法
        response = self.one_chat(prompt, **kwargs)

        # 处理响应
        predicted_prices = self._default_response_processor(response, num_of_predict, columns)

        # 将输出格式化为与输入相匹配
        if isinstance(stock_prices, pd.DataFrame):
            last_date = pd.to_datetime(stock_prices.index[-1])
            new_index = self._generate_future_index(last_date, num_of_predict, interval)
            return pd.DataFrame(predicted_prices, index=new_index)
        elif isinstance(stock_prices, pd.Series):
            last_date = pd.to_datetime(stock_prices.index[-1])
            new_index = self._generate_future_index(last_date, num_of_predict, interval)
            return pd.Series([p[columns[0]] for p in predicted_prices], index=new_index, name=stock_prices.name)
        else:
            return predicted_prices

    def _generate_future_index(self, last_date: pd.Timestamp, num_of_predict: int, interval: str) -> pd.DatetimeIndex:
        """生成未来的日期索引"""
        if interval == "分钟":
            return pd.date_range(start=last_date + pd.Timedelta(minutes=1), periods=num_of_predict, freq='T')
        elif interval == "小时":
            return pd.date_range(start=last_date + pd.Timedelta(hours=1), periods=num_of_predict, freq='H')
        elif interval == "天":
            return pd.date_range(start=last_date + pd.Timedelta(days=1), periods=num_of_predict, freq='D')
        elif interval == "周":
            return pd.date_range(start=last_date + pd.Timedelta(weeks=1), periods=num_of_predict, freq='W')
        elif interval == "月":
            return pd.date_range(start=last_date + pd.Timedelta(days=31), periods=num_of_predict, freq='M')
        else:
            raise ValueError(f"无效的间隔值: {interval}")

    def predict(self, x: Union[List, np.ndarray, pd.Series, pd.DataFrame], 
                num_of_predict: int, 
                data_processor: callable = None, 
                response_processor: callable = None,
                **kwargs) -> Union[List[float], np.ndarray, pd.Series, pd.DataFrame]:
        """
        预测时间序列的未来值，支持多列数据。

        参数：
        x (Union[List, np.ndarray, pd.Series, pd.DataFrame]): 输入的时间序列数据。
        num_of_predict (int): 要预测的未来值数量。
        data_processor (callable, 可选): 用于预处理输入数据的函数。
        response_processor (callable, 可选): 用于后处理LLM响应的函数。
        **kwargs: 传递给one_chat方法的额外关键字参数。

        返回：
        Union[List[float], np.ndarray, pd.Series, pd.DataFrame]: 与输入格式相同的预测值。
        """
        
        # 预处理输入数据
        if data_processor:
            x = data_processor(x)
        
        # 将输入转换为字符串表示
        if isinstance(x, pd.DataFrame):
            x_str = x.to_json(orient='split', date_format='iso')
            columns = x.columns.tolist()
        elif isinstance(x, pd.Series):
            x_str = x.to_json(orient='split', date_format='iso')
            columns = [x.name] if x.name else ['value']
        elif isinstance(x, np.ndarray):
            if x.ndim == 1:
                x_str = np.array2string(x, separator=', ')
                columns = ['value']
            else:
                x_str = np.array2string(x, separator=', ')
                columns = [f'column_{i}' for i in range(x.shape[1])]
        else:
            x_str = str(x)
            columns = ['value']
        
        # 构造提示词
        prompt = f"""给定以下时间序列数据：
{x_str}

数据包含以下列：{', '.join(columns)}

请预测该序列接下来的 {num_of_predict} 个时间点的值。
对于每个预测的时间点，请提供所有列的预测值。
请以JSON数组的形式提供您的答案，每个元素应该是一个包含所有列的对象。
不要包含任何额外的解释。

例如，如果数据包含 'open', 'close', 'high', 'low' 列，您的回答应该类似于：
[
    {{"open": 100.5, "close": 101.2, "high": 102.0, "low": 99.8}},
    {{"open": 101.3, "close": 102.1, "high": 102.8, "low": 100.9}},
    ...
]
"""

        # 调用one_chat方法
        response = self.one_chat(prompt, **kwargs)

        # 处理响应
        if response_processor:
            predicted_values = response_processor(response, num_of_predict)
        else:
            predicted_values = self._default_response_processor(response, num_of_predict, columns)

        # 将输出转换为与输入相匹配的格式
        if isinstance(x, pd.DataFrame):
            last_index = x.index[-1]
            new_index = pd.date_range(start=last_index + pd.Timedelta(days=1), periods=num_of_predict)
            return pd.DataFrame(predicted_values, index=new_index)
        elif isinstance(x, pd.Series):
            last_index = x.index[-1]
            new_index = pd.date_range(start=last_index + pd.Timedelta(days=1), periods=num_of_predict)
            return pd.Series([v[columns[0]] for v in predicted_values], index=new_index, name=x.name)
        elif isinstance(x, np.ndarray):
            return np.array([[v[col] for col in columns] for v in predicted_values])
        else:
            return [v[columns[0]] for v in predicted_values]

    def _default_response_processor(self, response: str, num_of_predict: int, columns: List[str]) -> List[Dict[str, float]]:
        """
        处理LLM响应的默认函数，支持多列数据。

        参数：
        response (str): LLM的原始响应字符串。
        num_of_predict (int): 期望的预测值数量。
        columns (List[str]): 数据列的名称。

        返回：
        List[Dict[str, float]]: 处理后的预测值列表，每个元素是一个字典，包含所有列的值。

        异常：
        ValueError: 当无法从响应中提取足够的有效数据时抛出。
        """
        try:
            predicted_values = json.loads(response)
            if isinstance(predicted_values, list) and len(predicted_values) >= num_of_predict:
                # 验证每个预测值是否包含所有必要的列
                for pred in predicted_values[:num_of_predict]:
                    if not all(col in pred for col in columns):
                        raise ValueError("预测值缺少一个或多个必要的列")
                return predicted_values[:num_of_predict]
        except json.JSONDecodeError:
            pass

        # 如果JSON解析失败或格式不正确，尝试从文本中提取数字
        numbers = re.findall(r"[-+]?\d*\.?\d+", response)
        if len(numbers) >= num_of_predict * len(columns):
            values = [float(num) for num in numbers]
            return [
                {col: values[i * len(columns) + j] for j, col in enumerate(columns)}
                for i in range(num_of_predict)
            ]

        raise ValueError(f"无法从响应中提取足够的有效数据。需要 {num_of_predict} 组预测，每组包含 {len(columns)} 个值。")

    def parse_and_store_compressed_history(self, compressed: str) -> List[Dict[str, str]]:
        try:
            # 尝试解析JSON
            data = json.loads(compressed)
            
            # 验证所需的键是否存在
            required_keys = ["topic", "key_points", "open_questions"]
            if not all(key in data for key in required_keys):
                raise ValueError("压缩历史记录中缺少必要的键")

            # 存储解析后的数据（这里只是一个示例，您可能需要根据实际需求调整存储方式）
            self.compressed_data = data

            # 创建压缩后的历史记录，确保至少有两个条目
            compressed_history = [
                {"role": "user", "content": "我们之前的聊天要点是什么？"},
                {"role": "assistant", "content": f"我们讨论的主要话题是：{data['topic']}。关键点包括：{', '.join(data['key_points'])}。" + (f"还有一些未解决的问题：{', '.join(data['open_questions'])}。" if data['open_questions'] else "")}
            ]

            return compressed_history

        except json.JSONDecodeError:
            # 如果JSON解析失败，返回基本的两个条目
            return [
                {"role": "user", "content": "我们之前的聊天要点是什么？"},
                {"role": "assistant", "content": "抱歉，我无法准确总结之前的对话。我们可以从这里重新开始我们的讨论。"}
            ]
        except Exception as e:
            # 处理其他可能的错误
            print(f"解析压缩历史记录时出错：{e}")
            return [
                {"role": "user", "content": "我们之前的聊天要点是什么？"},
                {"role": "assistant", "content": "在总结我们之前的对话时遇到了一些问题。我们可以从这里重新开始我们的讨论。"}
            ]

    def compress_history(self, history: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        使用 one_chat 方法压缩历史记录。
        这个方法需要在具体的 LLMApiClient 实现中重写，以适应特定的 API。
        """
        prompt = """
        请对以下对话历史进行高度概括和压缩：

        {history}

        请按照以下格式输出压缩后的结果：
        1. 主要话题：(简要描述主要讨论的话题)
        2. 关键点：(列出3-5个关键点，每个点不超过15字)
        3. 未解决问题：(如果有的话，列出1-2个未解决的问题)

        请确保输出的总字数不超过200字。输出应为JSON格式，键名分别为"topic", "key_points", "open_questions"。
        """

        history_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in history])
        compressed = self.one_chat(prompt.format(history=history_text))
        return self.parse_and_store_compressed_history(compressed)