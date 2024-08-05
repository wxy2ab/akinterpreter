

from typing import Any, Dict, Generator, Type
from core.blueprint._base_step_model import BaseStepModel
from core.blueprint._step_abstract import StepCodeGenerator, StepExecutor, StepInfoGenerator
from core.blueprint.code_generator.code_generator import CodeGenStepCodeGenerator
from core.blueprint.code_generator.step_executor import CodeGenStepExecutor
from core.blueprint.code_generator.step_model import CodeGenStepModel
from core.blueprint.llm_provider import LLMProvider
from core.planner.message import send_message
from core.utils import code_tools


class CodeGenInfoGenerator(StepInfoGenerator):
    def __init__(self):
        self.llm_provider = LLMProvider()
        self.llm_tools = self.llm_provider.new_code_runner()
        code_tools.add_with_recover("llm_tools",self.llm_tools)
        

    @property
    def step_description(self) -> str:
        return "提供python函数生成的步骤。生成的函数后续步骤可以调用。"
    
    @property
    def step_model(self) -> Type[BaseStepModel]:
        return CodeGenStepModel

    @property
    def step_code_generator(self) -> Type["StepCodeGenerator"]:
        return CodeGenStepCodeGenerator
    
    @property
    def step_executor(self) -> Type["StepExecutor"]:
        return CodeGenStepExecutor
    
    def get_step_model(self) -> BaseStepModel:
        return CodeGenStepModel()

    def gen_step_info(self, step_info :dict, query:str)-> Generator[Dict[str, Any], None, CodeGenStepModel]:
        step = CodeGenStepModel()
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