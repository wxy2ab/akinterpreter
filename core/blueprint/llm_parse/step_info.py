

from typing import Any, Dict, Generator, Type
from core.blueprint._base_step_model import BaseStepModel
from core.blueprint._step_abstract import StepCodeGenerator, StepExecutor, StepInfoGenerator
from core.blueprint.llm_parse.code_generator import LLMParseStepCodeGenerator
from core.blueprint.llm_parse.step_executor import LLMParseStepExecutor
from core.blueprint.llm_parse.step_model import LLMParseStepModel
from core.blueprint.llm_provider import LLMProvider
from core.planner.message import send_message
from core.utils.code_tools import code_tools


class LLMParseInfoGenerator(StepInfoGenerator):
    def __init__(self):
        self.llm_provider = LLMProvider()
        self.llm_tools = self.llm_provider.new_code_runner()
        code_tools.add_with_recover("llm_tools",self.llm_tools)
        

    @property
    def step_description(self) -> str:
        return "使用LLM解析数据"
    
    @property
    def step_model(self) -> Type[BaseStepModel]:
        return LLMParseStepModel

    @property
    def step_code_generator(self) -> Type["StepCodeGenerator"]:
        return LLMParseStepCodeGenerator
    
    @property
    def step_executor(self) -> Type["StepExecutor"]:
        return LLMParseStepExecutor
    
    def get_step_model(self) -> BaseStepModel:
        return LLMParseStepModel()

    def gen_step_info(self, step_info :dict, query:str)-> Generator[Dict[str, Any], None, LLMParseStepModel]:
        step = LLMParseStepModel()
        step.description = step_info["task"]
        step.save_data_to=step_info["save_data_to"]
        step.required_data=step_info["required_data"]
        yield send_message(type="plan",content="\n优化变量控制\n")
        yield send_message(type="plan",content="完成步骤\n")
        return step

    def validate_step_info(self, step_info:dict)-> tuple[str, bool]:
        required_data = step_info.get("required_data")
        save_data_to = step_info.get("save_data_to")

        return "",True

    def fix_step_info(self, step_data, query, error_msg) -> Generator[Dict[str, Any], None, None]:
        yield send_message("fix finieshed", "message")