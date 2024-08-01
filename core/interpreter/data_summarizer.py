from collections import OrderedDict, defaultdict, namedtuple
from datetime import date, datetime
from typing import Any, Dict, List, Tuple, Union
import numpy as np
import pandas as pd


class DataSummarizer:
    @staticmethod
    def get_data_summary(data: Union[pd.DataFrame, Dict[str, pd.DataFrame], list, np.ndarray, tuple , set ,Any], max_depth: int = 5) -> str:
        if isinstance(data, dict) and all(isinstance(v, pd.DataFrame) for v in data.values()):
            return DataSummarizer.get_multiple_dataframes_summary(data)
        elif isinstance(data, dict):
            return DataSummarizer.get_dict_summary(data)
        elif isinstance(data, pd.DataFrame):
            return DataSummarizer.get_dataframe_summary(data)
        elif isinstance(data, np.ndarray):
            return DataSummarizer.get_numpy_array_summary(data)
        elif isinstance(data, list):
            return DataSummarizer.get_list_summary(data)
        elif isinstance(data, tuple):
            return DataSummarizer.get_tuple_summary(data, max_depth)
        elif isinstance(data, set):
            return DataSummarizer.get_set_summary(data)
        elif DataSummarizer.is_namedtuple(data):
            return DataSummarizer.get_namedtuple_summary(data)
        elif isinstance(data, OrderedDict):
            return DataSummarizer.get_ordereddict_summary(data, max_depth)
        elif isinstance(data, defaultdict):
            return DataSummarizer.get_defaultdict_summary(data, max_depth)
        elif isinstance(data, (datetime, date)):
            return DataSummarizer.get_datetime_summary(data)
        elif callable(data):
            return DataSummarizer.get_function_summary(data)
        else:
            return f"数据类型: {type(data)}\n样本: {str(data)[:1000]}"
    @staticmethod
    def is_namedtuple(x):
        return isinstance(x, tuple) and hasattr(x, '_fields') and hasattr(x, '_asdict')
    
    @staticmethod
    def get_dict_summary(data: Dict[str, Any], max_depth: int = 3) -> str:
        def get_schema(d: Dict[str, Any], depth: int = 0) -> str:
            if depth >= max_depth:
                return "..."

            schema = "{\n"
            for key, value in d.items():
                schema += f"{'  ' * (depth + 1)}{key}: "
                if isinstance(value, dict):
                    schema += get_schema(value, depth + 1)
                elif isinstance(value, list):
                    if value and isinstance(value[0], dict):
                        schema += f"[{get_schema(value[0], depth + 1)}]"
                    else:
                        schema += f"List[{type(value[0]).__name__}]"
                else:
                    schema += type(value).__name__
                schema += ",\n"
            schema += f"{'  ' * depth}}}"
            return schema

        summary = f"数据类型: 字典\n"
        summary += f"键的数量: {len(data)}\n"
        summary += "Schema:\n"
        summary += get_schema(data)
        return summary
    
    @staticmethod
    def get_multiple_dataframes_summary(data_dict: Dict[str, pd.DataFrame]) -> str:
        summary = "数据类型: 多个DataFrame\n\n"
        for name, df in data_dict.items():
            summary += f"DataFrame: {name}\n"
            summary += DataSummarizer.get_dataframe_summary(df)
            summary += "\n" + "-"*50 + "\n\n"
        return summary

    @staticmethod
    def get_dataframe_summary(df: pd.DataFrame) -> str:
        summary = f"数据类型: pandas DataFrame\n"
        summary += f"形状: {df.shape}\n"
        summary += f"列: {', '.join(df.columns)}\n"
        summary += "数据类型:\n"
        for col, dtype in df.dtypes.items():
            summary += f"  {col}: {dtype}\n"
        summary += "样本数据 (前5行):\n"
        summary += df.head().to_string()
        summary += "\n\n描述性统计:\n"
        summary += df.describe(include='all').to_string()
        summary += "\n\n缺失值信息:\n"
        summary += df.isnull().sum().to_string()
        return summary

    @staticmethod
    def get_numpy_array_summary(arr: np.ndarray) -> str:
        summary = f"数据类型: NumPy array\n"
        summary += f"形状: {arr.shape}\n"
        summary += f"数据类型: {arr.dtype}\n"
        summary += f"样本数据 (前10个元素): {arr.flatten()[:10]}\n"
        summary += f"描述性统计:\n"
        summary += f"  最小值: {np.min(arr)}\n"
        summary += f"  最大值: {np.max(arr)}\n"
        summary += f"  平均值: {np.mean(arr)}\n"
        summary += f"  中位数: {np.median(arr)}\n"
        summary += f"  标准差: {np.std(arr)}\n"
        return summary

    @staticmethod
    def get_list_summary(data: List) -> str:
        summary = f"数据类型: List\n"
        summary += f"长度: {len(data)}\n"
        summary += f"样本数据 (前10个元素): {data[:10]}\n"
        if all(isinstance(item, (int, float)) for item in data):
            summary += "数值列表的描述性统计:\n"
            summary += f"  最小值: {min(data)}\n"
            summary += f"  最大值: {max(data)}\n"
            summary += f"  平均值: {sum(data) / len(data)}\n"
            summary += f"  中位数: {sorted(data)[len(data)//2]}\n"
        return summary

    @staticmethod
    def get_tuple_summary(data: Tuple, max_depth: int = 3) -> str:
        summary = f"数据类型: 元组 (Tuple)\n"
        summary += f"长度: {len(data)}\n"
        summary += "元素类型:\n"
        for i, item in enumerate(data):
            summary += f"  {i}: {DataSummarizer.get_type_info(item, max_depth - 1)}\n"
        return summary

    @staticmethod
    def get_set_summary(data: set) -> str:
        summary = f"数据类型: 集合 (Set)\n"
        summary += f"元素数量: {len(data)}\n"
        if len(data) > 0:
            sample = list(data)[:5]
            summary += f"样本元素 (最多5个): {sample}\n"
            summary += f"元素类型: {type(next(iter(data))).__name__}\n"
        return summary

    @staticmethod
    def get_namedtuple_summary(data: namedtuple) -> str:
        summary = f"数据类型: 命名元组 (namedtuple)\n"
        summary += f"名称: {type(data).__name__}\n"
        summary += "字段:\n"
        for field in data._fields:
            summary += f"  {field}: {type(getattr(data, field)).__name__}\n"
        return summary

    @staticmethod
    def get_ordereddict_summary(data: OrderedDict, max_depth: int = 3) -> str:
        summary = f"数据类型: 有序字典 (OrderedDict)\n"
        summary += f"键的数量: {len(data)}\n"
        summary += "键值对 (前5个):\n"
        for i, (key, value) in enumerate(list(data.items())[:5]):
            summary += f"  {key}: {DataSummarizer.get_type_info(value, max_depth - 1)}\n"
            if i == 4:
                break
        return summary

    @staticmethod
    def get_defaultdict_summary(data: defaultdict, max_depth: int = 3) -> str:
        summary = f"数据类型: 默认字典 (defaultdict)\n"
        summary += f"默认工厂函数: {data.default_factory.__name__ if data.default_factory else 'None'}\n"
        summary += f"键的数量: {len(data)}\n"
        summary += "键值对 (前5个):\n"
        for i, (key, value) in enumerate(list(data.items())[:5]):
            summary += f"  {key}: {DataSummarizer.get_type_info(value, max_depth - 1)}\n"
            if i == 4:
                break
        return summary

    @staticmethod
    def get_datetime_summary(data: Union[datetime, date]) -> str:
        summary = f"数据类型: {'datetime' if isinstance(data, datetime) else 'date'}\n"
        summary += f"值: {data.isoformat()}\n"
        if isinstance(data, datetime):
            summary += f"时区信息: {data.tzinfo}\n"
        return summary

    @staticmethod
    def get_function_summary(data: callable) -> str:
        import inspect
        summary = f"数据类型: 函数\n"
        summary += f"函数名: {data.__name__}\n"
        signature = inspect.signature(data)
        summary += f"参数: {signature}\n"
        if data.__doc__:
            summary += f"文档字符串: {data.__doc__[:100]}...\n" if len(data.__doc__) > 100 else f"文档字符串: {data.__doc__}\n"
        return summary

    @staticmethod
    def get_type_info(value: Any, depth: int) -> str:
        if depth <= 0:
            return type(value).__name__
        if isinstance(value, dict):
            return f"Dict[{len(value)} keys]"
        elif isinstance(value, list):
            return f"List[{len(value)} items]"
        elif isinstance(value, tuple):
            return f"Tuple[{len(value)} items]"
        elif isinstance(value, set):
            return f"Set[{len(value)} items]"
        elif isinstance(value, pd.DataFrame):
            return f"DataFrame[{value.shape[0]} rows x {value.shape[1]} columns]"
        elif isinstance(value, np.ndarray):
            return f"ndarray[shape={value.shape}, dtype={value.dtype}]"
        else:
            return type(value).__name__