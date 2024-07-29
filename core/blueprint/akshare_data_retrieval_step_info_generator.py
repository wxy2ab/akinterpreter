from typing import Type

from core.blueprint._base_step_model import BaseStepModel
from core.blueprint.akshare_data_retrieval_step_model import AkShareDataRetrievalStepModel
from ._step_abstract import StepInfoGenerator
from .akshare_data_retrieval_step_model import AkShareDataRetrievalStepModel


class AkShareDataRetrievalStepInfoGenerator(StepInfoGenerator):
    @property
    def step_description(self) -> str:
        return "提供股票数据,期货数据,期权数据,债券数据,外汇数据,宏观经济数据,基金数据,指数数据,另类数据,新闻数据,港股数据,美股数据,金融工具,数据工具,行业数据,公司数据,交易所数据,市场情绪数据等财经方面的资讯和数据"
    
    @property
    def step_model(self) -> Type[BaseStepModel]:
        return AkShareDataRetrievalStepModel
    
    def gen_step_info(self, step_data_type, query):
        pass

    def validate_step_info(self, step_data):
        pass

    def fix_step_info(self, step_data, query, error_msg):
        pass