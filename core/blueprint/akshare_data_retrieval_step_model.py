

from typing import Literal
from ._base_step_model import BaseStepModel


class AkShareDataRetrievalStepModel(BaseStepModel):
    step_type: Literal['data_retrieval'] = 'data_retrieval'
    data_category: Literal[
        "股票数据", "期货数据", "期权数据", "债券数据", "外汇数据", 
        "宏观经济数据", "基金数据", "指数数据", "另类数据", "新闻数据", 
        "港股数据", "美股数据", "金融工具", "数据工具", "行业数据",
        "公司数据", "交易所数据", "市场情绪数据", "其他数据"
    ]
