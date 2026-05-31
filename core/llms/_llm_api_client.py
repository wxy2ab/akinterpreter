from __future__ import annotations

from abc import ABC, abstractmethod
import re
from typing import Generator, Iterator, List, Dict, Any, Union
import json
from ..utils.log import logger

try:
    import pandas as pd
except ModuleNotFoundError:
    pd = None

try:
    import numpy as np
except ModuleNotFoundError:
    np = None


def _require_optional_time_series_dependencies():
    missing = []
    if pd is None:
        missing.append("pandas")
    if np is None:
        missing.append("numpy")
    if missing:
        raise ModuleNotFoundError(
            "LLMApiClient time-series prediction helpers require optional "
            f"dependencies: {', '.join(missing)}"
        )
    return pd, np

class LLMApiClient(ABC):

    supports_structured_output: bool = False

    def set_history(self, history: List[Dict[str, str]]):
        if not hasattr(self, "history"):
            self.history = []
        self.history = history

    def set_response_format(self, fmt: Union[Dict[str, Any], None]) -> None:
        """Enable / disable structured output for subsequent chat calls.

        ``fmt`` is one of:
            * ``{"type": "json_object"}`` — any JSON, no schema
            * ``{"type": "json_schema", "json_schema": {...}}`` — strict schema
            * ``None`` — disable

        Subclasses that set ``supports_structured_output = True`` MUST
        override this to wire ``fmt`` into the next API request. The base
        class is a no-op so unsupported clients silently degrade to
        prompt-only discipline.
        """
        pass

    def get_response_format(self) -> Union[Dict[str, Any], None]:
        return getattr(self, "_response_format", None)

    def json_chat(
        self,
        message: str,
        *,
        schema: Union[Dict[str, Any], None] = None,
        reset_after: bool = True,
        parse: bool = True,
    ) -> Union[Dict[str, Any], List[Any], str]:
        """One-shot JSON-mode chat with automatic parsing.

        Flow: enable response_format (if supported) → one_chat → parse JSON
        with brace-substring fallback → optionally restore prior format.
        Clients that don't support structured output still attempt to
        parse the result, relying on prompt-level discipline.
        """
        prior_fmt = self.get_response_format()
        if self.supports_structured_output:
            if schema is not None:
                self.set_response_format({
                    "type": "json_schema",
                    "json_schema": schema,
                })
            else:
                self.set_response_format({"type": "json_object"})
        try:
            raw = self.one_chat(message)
            if not parse:
                return raw
            return _parse_json_lenient(raw)
        finally:
            if reset_after:
                self.set_response_format(prior_fmt)

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

    def tool_invoke(self, messages: List[Dict[str, str]], tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        将消息和工具定义发送给 API，返回结构化响应。

        与 tool_chat 的区别：
        - 不自动执行工具，不修改 history
        - 接受完整的 messages 列表（包含 system/user）
        - 返回 dict: {"content": str, "tool_calls": list[dict]}
          其中 tool_calls 每项格式: {"tool_name": str, "arguments": dict, "tool_use_id": str}

        子类应当覆写此方法。默认实现通过 tool_chat 做兼容处理。
        """
        raise NotImplementedError(
            f"{type(self).__name__} does not implement tool_invoke. "
            "Override this method to support structured tool calling."
        )

    def _safe_parse_tool_arguments(self, arguments: Any) -> Dict[str, Any]:
        if arguments in (None, ""):
            return {}
        if isinstance(arguments, dict):
            return arguments
        if isinstance(arguments, str):
            try:
                parsed = json.loads(arguments)
            except json.JSONDecodeError:
                return {"raw_input": arguments}
            return parsed if isinstance(parsed, dict) else {"raw_input": parsed}
        return {"raw_input": arguments}

    def _normalize_tool_calls(self, tool_calls: Any) -> List[Dict[str, Any]]:
        normalized_calls: List[Dict[str, Any]] = []
        for index, tool_call in enumerate(tool_calls or []):
            if isinstance(tool_call, dict):
                function_info = tool_call.get("function") or {}
                tool_name = function_info.get("name") or tool_call.get("name") or ""
                arguments = function_info.get("arguments")
                if arguments is None:
                    arguments = tool_call.get("input")
                tool_use_id = tool_call.get("id") or tool_call.get("tool_use_id") or str(index)
            else:
                function_info = getattr(tool_call, "function", None)
                tool_name = getattr(function_info, "name", "") if function_info is not None else getattr(tool_call, "name", "")
                arguments = getattr(function_info, "arguments", None) if function_info is not None else None
                if arguments is None:
                    arguments = getattr(tool_call, "input", None)
                tool_use_id = getattr(tool_call, "id", "") or getattr(tool_call, "tool_use_id", "") or str(index)

            normalized_calls.append({
                "tool_name": tool_name,
                "arguments": self._safe_parse_tool_arguments(arguments),
                "tool_use_id": tool_use_id,
            })
        return normalized_calls

    def _normalize_tool_invoke_response(
        self,
        content: Any = "",
        tool_calls: Any = None,
        **metadata: Any,
    ) -> Dict[str, Any]:
        payload = {
            "content": "" if content is None else str(content),
            "tool_calls": self._normalize_tool_calls(tool_calls),
        }
        for key, value in metadata.items():
            if value is not None:
                payload[key] = value
        return payload

    def _messages_to_prompt(self, messages: List[Dict[str, Any]]) -> str:
        prompt_parts: List[str] = []
        for message in messages or []:
            role = message.get("role") or message.get("Role") or "user"
            content = message.get("content")
            if content is None:
                content = message.get("Content")
            if isinstance(content, list):
                flattened_parts: List[str] = []
                for part in content:
                    if isinstance(part, dict):
                        text = part.get("text") or part.get("content")
                        if text is None:
                            text = json.dumps(part, ensure_ascii=False)
                        flattened_parts.append(str(text))
                    else:
                        flattened_parts.append(str(part))
                content = "\n".join(flattened_parts)
            prompt_parts.append(f"{role}: {content}")
        return "\n\n".join(prompt_parts)

    def _tool_invoke_via_one_chat(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        try:
            response = self.one_chat(messages, is_stream=False)
        except Exception:
            response = self.one_chat(self._messages_to_prompt(messages), is_stream=False)

        if isinstance(response, dict):
            return {
                "content": str(response.get("content", "")),
                "tool_calls": response.get("tool_calls", []),
            }
        if isinstance(response, str):
            content = response
        else:
            content = "".join(response)
        return {"content": content, "tool_calls": []}

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
    def set_system_message(self, system_message: str = "你是一个智能助手,擅长把复杂问题清晰明白通俗易懂地解答出来"):
        if not hasattr(self, "history"):
            self.history = []
        self.history = [{"role": "system", "content": system_message}]
        
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
        _require_optional_time_series_dependencies()
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
        _require_optional_time_series_dependencies()
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
        _require_optional_time_series_dependencies()
        
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
            
            # 🔧 支持新的简化格式（只有summary键）和旧格式（topic/key_points/open_questions）
            if "summary" in data:
                # 新格式：只有一个summary键
                summary_content = data['summary']
                # 存储解析后的数据
                self.compressed_data = data
                # 创建超级简洁的压缩历史（只用一条消息）
                compressed_history = [
                    {"role": "user", "content": f"[已压缩历史] {summary_content}"}
                ]
            elif all(key in data for key in ["topic", "key_points", "open_questions"]):
                # 旧格式：兼容性支持
                self.compressed_data = data
                compressed_history = [
                    {"role": "user", "content": "我们之前的聊天要点是什么？"},
                    {"role": "assistant", "content": f"我们讨论的主要话题是：{data['topic']}。关键点包括：{', '.join(data['key_points'])}。" + (f"还有一些未解决的问题：{', '.join(data['open_questions'])}。" if data['open_questions'] else "")}
                ]
            else:
                raise ValueError("压缩历史记录格式不正确")

            return compressed_history

        except json.JSONDecodeError:
            # 如果JSON解析失败，返回基本的一条消息
            logger.warning("JSON解析失败，使用原始文本作为压缩历史")
            return [
                {"role": "user", "content": f"[已压缩历史] {compressed[:100]}"}  # 只保留前100字符
            ]
        except Exception as e:
            # 处理其他可能的错误
            logger.warning(f"解析压缩历史记录时出错：{e}")
            return [
                {"role": "user", "content": "[已压缩历史] 早期对话已被压缩，继续当前任务。"}
            ]

    def compress_history(self, history: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        使用 one_chat 方法压缩历史记录。
        这个方法需要在具体的 LLMApiClient 实现中重写，以适应特定的 API。
        
        🔧 修复：加入基于消息长度的判断，避免不必要的压缩
        """
        # 🔧 修复：先检查是否真的需要压缩
        # 计算历史消息的总长度（估算token数）
        total_chars = sum(len(str(msg.get('content', ''))) for msg in history)
        estimated_tokens = total_chars
        
        # 如果消息总长度较小，无需压缩，直接返回
        # 保守阈值：< 15K tokens 或 消息数 < 15 条
        if estimated_tokens < 15000 and len(history) < 15:
            logger.info(f"历史消息总长度较小(约{estimated_tokens:,}tokens, {len(history)}条)，无需压缩")
            return history
        
        logger.info(f"历史消息总长度较大(约{estimated_tokens:,}tokens, {len(history)}条)，开始使用LLM压缩")
        
        # 🔧 更激进的压缩提示：限制输出为100字以内的一句话摘要
        prompt = """
        请将以下对话历史压缩为一句话摘要（不超过100字）：

        {history}

        要求：
        1. 只保留最关键的信息（如：目标、当前进度、最新结果）
        2. 省略所有细节和中间过程
        3. 用一句话概括即可
        4. 输出格式：JSON，只包含一个键 "summary"

        示例输出：{{"summary": "正在优化策略，目标夏普率2.5，当前已完成5次迭代，最佳结果2.1"}}
        """

        # 🔧 优化历史文本格式：只保留content，去掉tool_calls等冗余信息
        history_text = "\n".join([f"{msg['role']}: {str(msg.get('content', ''))[:200]}" for msg in history])  # 每条消息只保留前200字符
        compressed = self.one_chat(prompt.format(history=history_text))
        
        compressed_history = self.parse_and_store_compressed_history(compressed)
        
        # 验证压缩效果
        compressed_chars = sum(len(str(msg.get('content', ''))) for msg in compressed_history)
        logger.info(f"压缩完成: {len(compressed_history)}条消息, 约{compressed_chars:,}tokens")

        return compressed_history


def _parse_json_lenient(raw: Any) -> Any:
    """Tolerant JSON parser used by ``LLMApiClient.json_chat``.

    Order of attempts: direct ``json.loads`` → strip ```` ```...``` ```` code
    fence → curly brace substring → square brace substring. Raises
    ``ValueError`` if no variant parses.
    """
    if raw is None:
        raise ValueError("empty response from LLM")
    text = str(raw).strip()
    if text.startswith("```"):
        first_nl = text.find("\n")
        last_fence = text.rfind("```")
        if first_nl != -1 and last_fence > first_nl:
            text = text[first_nl + 1:last_fence].strip()
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        pass
    for opener, closer in (("{", "}"), ("[", "]")):
        start = text.find(opener)
        end = text.rfind(closer)
        if 0 <= start < end:
            try:
                return json.loads(text[start:end + 1])
            except (json.JSONDecodeError, ValueError):
                continue
    raise ValueError(f"could not parse JSON from LLM response: {text[:240]!r}")
