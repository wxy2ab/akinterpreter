
from typing import Any, Dict, Generator, Type

from .llm_provider import LLMProvider

from ._base_step_model import BaseStepModel
from ..planner.message import send_message
from ._step_abstract import StepExecutor, StepInfoGenerator
from .data_analysis_step_model import DataAnalysisStepModel
from ._step_abstract import StepCodeGenerator
from .data_analysis_step_code_code_generator import DataAnalysisStepCodeGenerator


class DataAnalysisStepInfoGenerator(StepInfoGenerator):
    def __init__(self) -> None:
        self.llm_provider = LLMProvider()
        self.llm_client = self.llm_provider.new_llm_client()
        self.llm_cheap_client  = self.llm_provider.new_cheap_client()

    @property
    def step_description(self) -> str:
        return "提供数据统计分析的步骤"
    
    @property
    def step_model(self) -> Type[BaseStepModel]:
        return DataAnalysisStepModel

    @property
    def step_code_generator(self) -> Type["StepCodeGenerator"]:
        return DataAnalysisStepCodeGenerator
    
    @property
    def step_executor(self) -> Type["StepExecutor"]:
        pass
    
    def get_step_model(self) -> BaseStepModel:
        return DataAnalysisStepModel()

    def gen_step_info(self, step_info :dict, query:str)-> Generator[Dict[str, Any], None, DataAnalysisStepModel]:
        step = DataAnalysisStepModel()
        step.description = step_info["task"]
        step.save_data_to=step_info["save_data_to"]
        step.required_data=step_info["required_data"]
        yield send_message(type="plan",content="优化变量控制")
        yield send_message(type="plan",content="完成步骤")
        return step

    def validate_step_info(self, step_info:dict)-> tuple[str, bool]:
        return "",True

    def fix_step_info(self, step_data, query, error_msg) -> Generator[Dict[str, Any], None, None]:
        yield send_message("fix finieshed", "error")