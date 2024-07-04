from typing import Any, Dict, List, Union
import numpy as np
import pandas as pd


class DataSummarizer:
    @staticmethod
    def get_data_summary(data: Union[pd.DataFrame, Dict[str, pd.DataFrame], List, np.ndarray, Any]) -> str:
        if isinstance(data, dict) and all(isinstance(v, pd.DataFrame) for v in data.values()):
            return DataSummarizer.get_multiple_dataframes_summary(data)
        elif isinstance(data, pd.DataFrame):
            return DataSummarizer.get_dataframe_summary(data)
        elif isinstance(data, np.ndarray):
            return DataSummarizer.get_numpy_array_summary(data)
        elif isinstance(data, list):
            return DataSummarizer.get_list_summary(data)
        else:
            return f"数据类型: {type(data)}\n样本: {str(data)[:1000]}"

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