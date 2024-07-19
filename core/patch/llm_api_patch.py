from ..akshare_doc.akshare_data_singleton import AKShareDataSingleton
from ..utils.config_setting import Config


def predict_patch():
    single = AKShareDataSingleton()
    single.classified_functions["数据工具"].append("llm_client.predict: 使用LLM API预测未来股价(或者时序序列)")
    single.akshare_docs["llm_client.predict"]="""
# llm_client.predict 函数文档

## 概述

`predict` 函数是 `llm_client` 的一个方法，用于预测时间序列数据的未来值。这个函数能够处理各种类型的输入数据，包括单变量和多变量时间序列，并支持自定义的数据预处理和响应后处理。

## 函数签名

```python
def predict(self, 
            x: Union[List, np.ndarray, pd.Series, pd.DataFrame], 
            num_of_predict: int, 
            data_processor: Callable = None, 
            response_processor: Callable = None) -> Union[List[float], np.ndarray, pd.Series, pd.DataFrame]:
```

## 参数

- `x` (Union[List, np.ndarray, pd.Series, pd.DataFrame]): 
  输入的时间序列数据。可以是以下类型之一：
  - List：一维数字列表
  - numpy.ndarray：一维或二维数组
  - pandas.Series：带有时间索引的系列数据
  - pandas.DataFrame：带有时间索引的多列数据（如股票的开盘价、收盘价等）

- `num_of_predict` (int): 
  要预测的未来时间点数量。

- `data_processor` (Callable, 可选): 
  用于预处理输入数据的函数。这个函数应该接受 `x` 作为输入，并返回处理后的数据。

- `response_processor` (Callable, 可选): 
  用于后处理 LLM 响应的函数。这个函数应该接受原始响应字符串和 `num_of_predict` 作为输入，并返回处理后的预测值。


## 返回值

函数返回与输入格式相匹配的预测值：

- 如果输入是 List 或一维 numpy.ndarray，返回 List[float]
- 如果输入是二维 numpy.ndarray，返回二维 numpy.ndarray
- 如果输入是 pandas.Series，返回具有预测时间索引的 pandas.Series
- 如果输入是 pandas.DataFrame，返回具有预测时间索引的 pandas.DataFrame

返回的数据包含 `num_of_predict` 个预测时间点的值。

## 异常

- ValueError: 当无法从 LLM 响应中提取足够的有效数据时抛出。
- TypeError: 当输入数据类型不支持时抛出。
- 可能由 data_processor 或 response_processor 抛出的任何异常。

## 工作流程

1. 如果提供了 `data_processor`，使用它预处理输入数据。
2. 将输入数据转换为适合 llm_client 处理的字符串格式。
3. 构造提示词，包含输入数据和预测要求。
4. 调用 llm_client 的 `one_chat` 方法获取预测结果。
5. 如果提供了 `response_processor`，使用它处理 llm_client 的响应；否则使用默认的响应处理器。
6. 将处理后的预测结果转换为与输入格式匹配的格式。

## 使用示例

### 1. 简单的一维数据预测

```python
#直接用llm_client 或者用 client=llm_factory.get_instance()
data = [1, 2, 3, 4, 5]
predictions = llm_client.predict(data, num_of_predict=3)
print(predictions)  # 输出可能是 [6, 7, 8]
```

### 2. 使用 pandas Series 进行预测

```python
import pandas as pd

#直接用llm_client 或者用 client=llm_factory.get_instance()
dates = pd.date_range(start='2023-01-01', periods=5)
series = pd.Series([100, 101, 103, 102, 104], index=dates)
predictions = llm_client.predict(series, num_of_predict=3)
print(predictions)
```

### 3. 多变量时间序列预测（如股票数据）

```python
import pandas as pd

#直接用llm_client 或者用 client=llm_factory.get_instance()
dates = pd.date_range(start='2023-01-01', periods=5)
df = pd.DataFrame({
    'open': [100, 101, 102, 101, 103],
    'close': [101, 102, 103, 102, 104],
    'volume': [1000, 1100, 1050, 900, 1200]
}, index=dates)
predictions = llm_client.predict(df, num_of_predict=2)
print(predictions)
```

### 4. 使用自定义数据处理器

```python
def custom_processor(data):
    return (data - data.mean()) / data.std()  # 标准化数据

#直接用llm_client 或者用 client=llm_factory.get_instance()
data = [1, 2, 3, 4, 5]
predictions = llm_client.predict(data, num_of_predict=3, data_processor=custom_processor)
print(predictions)
```

### 5. 使用额外的 LLM 参数

```python
#直接用llm_client 或者用 client=llm_factory.get_instance()
data = [1, 2, 3, 4, 5]
predictions = llm_client.predict(data, num_of_predict=3, temperature=0.7, max_tokens=100)
print(predictions)
```

## 注意事项

- 确保输入数据的质量和格式正确，以获得最佳预测结果。
- 对于大型或复杂的数据集，考虑使用 `data_processor` 进行预处理，如标准化或特征选择。
使用llm_client和llm_factory 不需要导入，可以直接使用
"""


def predict_with_news_patch():

    single = AKShareDataSingleton()
    single.classified_functions["数据工具"].append("llm_client.predict_with_news: 基于LLM API 使用新闻内容和股价来预测未来股价(或者时序序列), 这个函数需要提供新闻数据效果更好")
    single.akshare_docs["llm_client.predict_with_news"]="""
predict_with_news 函数是 llm_client 类的一个方法，用于结合历史股票价格数据和相关新闻信息来预测未来的股票价格。这个函数能够处理多种类型的股票数据输入，包括单一价格序列和多维度的股票数据（如开盘价、收盘价、最高价、最低价和交易量）。
函数签名
def predict_with_news(self, 
                      stock_prices: Union[List[float], pd.Series, pd.DataFrame],
                      news_data: List[Dict[str, str]],
                      num_of_predict: int,
                      stock_symbol: str = "",
                      interval: str = "天") -> Union[List[Dict[str, float]], pd.Series, pd.DataFrame]:
参数

stock_prices (Union[List[float], pd.Series, pd.DataFrame]):
历史股票价格数据。可以是以下类型之一：

List[float]：一维价格列表
pandas.Series：带有时间索引的单一价格序列
pandas.DataFrame：带有时间索引的多列股票数据（如开盘价、收盘价、最高价、最低价、交易量）


news_data (List[Dict[str, str]]):
包含相关新闻数据的字典列表。每个字典应包含 'date' 和 'headline' 键。
例如：[{'date': '2023-01-01', 'headline': '公司 XYZ 发布新产品'}]
num_of_predict (int):
要预测的未来时间点数量。
stock_symbol (str, 可选):
股票代码或公司名称，用于提供上下文。默认为空字符串。
interval (str, 可选):
数据的时间间隔。可选值为 "分钟"、"小时"、"天"、"周"、"月"。默认为 "天"。
**kwargs:
传递给 one_chat 方法的额外关键字参数，用于控制 LLM 的行为（如 temperature、max_tokens 等）。

返回值
函数返回与输入格式相匹配的预测值：

如果输入是 List[float]，返回 List[Dict[str, float]]，其中每个字典包含预测的价格
如果输入是 pandas.Series，返回具有预测时间索引的 pandas.Series
如果输入是 pandas.DataFrame，返回具有预测时间索引的 pandas.DataFrame，包含所有输入列的预测值

返回的数据包含 num_of_predict 个预测时间点的值。
异常

ValueError: 当无法从 LLM 响应中提取足够的有效数据时抛出，或当提供了无效的 interval 值时抛出。
TypeError: 当输入数据类型不支持时抛出。

工作流程

验证输入参数，特别是 interval 的有效性。
处理输入的股票价格数据，将其转换为适合 LLM 处理的字符串格式。
格式化新闻数据，选择最近的几条新闻。
构造包含股票数据、新闻信息和预测要求的提示词。
调用 llm_client 的 one_chat 方法获取预测结果。
处理 llm_client 的响应，提取预测的股票数据。
将处理后的预测结果转换为与输入格式匹配的格式，并生成相应的时间索引。

使用示例
1. 使用单一价格序列进行预测
import pandas as pd

#直接用llm_client 或者用 client=llm_factory.get_instance()

# 创建股票价格数据
dates = pd.date_range(start='2023-01-01', periods=5)
prices = pd.Series([100, 101, 102, 101, 103], index=dates, name='price')

# 创建新闻数据
news = [
    {'date': '2023-01-02', 'headline': '公司 XYZ 宣布裁员计划'},
    {'date': '2023-01-04', 'headline': 'XYZ 股票创下新高'}
]

# 进行预测
predictions = 直接用llm_client.predict_with_news(prices, news, num_of_predict=3, stock_symbol='XYZ')
print(predictions)
2. 使用多维度股票数据进行预测
import pandas as pd

#直接用llm_client 或者用 client=llm_factory.get_instance()

# 创建多维度股票数据
dates = pd.date_range(start='2023-01-01', periods=5)
stock_data = pd.DataFrame({
    'open': [100, 101, 102, 101, 103],
    'close': [101, 102, 103, 102, 104],
    'high': [102, 103, 104, 103, 105],
    'low': [99, 100, 101, 100, 102],
    'volume': [1000000, 1100000, 1050000, 900000, 1200000]
}, index=dates)

# 创建新闻数据
news = [
    {'date': '2023-01-02', 'headline': 'XYZ公司推出革命性新产品'},
    {'date': '2023-01-04', 'headline': 'XYZ公司季度财报超出市场预期'}
]

# 进行预测
predictions = llm_client.predict_with_news(stock_data, news, num_of_predict=3, stock_symbol='XYZ', interval='天')
print(predictions)
3. 使用不同的时间间隔
# 使用小时级别的数据
hourly_data = pd.Series([100, 101, 102], index=pd.date_range(start='2023-01-01', periods=3, freq='H'), name='price')
hourly_news = [{'date': '2023-01-01 01:00:00', 'headline': 'XYZ公司股票在盘中创新高'}]

hourly_predictions = llm_client.predict_with_news(hourly_data, hourly_news, num_of_predict=3, interval='小时')
print(hourly_predictions)
4. 使用额外的 LLM 参数
predictions = llm_client.predict_with_news(
    stock_data, 
    news, 
    num_of_predict=3, 
    stock_symbol='XYZ'
)
print(predictions)
注意事项

确保提供的股票价格数据和新闻数据的时间范围相互匹配，以获得最佳预测效果。
新闻数据的质量和相关性对预测结果有重要影响。尽量提供与股票直接相关的重要新闻。
使用llm_client和llm_factory 不需要导入，可以直接使用
"""
