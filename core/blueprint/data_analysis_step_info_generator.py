
from typing import Any, Dict, Generator, Type

from ._base_step_model import BaseStepModel
from ..planner.message import send_message
from ._step_abstract import StepInfoGenerator
from .data_analysis_step_model import DataAnalysisStepModel


class DataAnalysisStepInfoGenerator(StepInfoGenerator):
    @property
    def step_description(self) -> str:
        return "提供数据统计分析的步骤"
    
    @property
    def step_model(self) -> Type[BaseStepModel]:
        return DataAnalysisStepModel
    
    def get_step_model(self) -> BaseStepModel:
        return DataAnalysisStepModel()

    def gen_step_info(self, step_info :dict, query:str)-> Generator[Dict[str, Any], None, BaseStepModel]:
        step = DataAnalysisStepModel()
        step.description = step_info["task"]
        step.save_data_to=step_info["save_data_to"]
        step.required_data=step_info["required_data"]
        yield send_message(type="plan",content="优化变量控制")
        yield send_message(type="plan",content="完成步骤")
        return step

    def validate_step_info(self, step_data):
        pass

    def fix_step_info(self, step_data, query, error_msg):
        pass