

from typing import Any, Dict, Generator, Type
from core.blueprint._base_step_model import BaseStepModel
from core.blueprint._step_abstract import StepCodeGenerator, StepExecutor, StepInfoGenerator
from core.blueprint.astock.code_generator import AStockQueryStepCodeGenerator
from core.blueprint.astock.step_executor import AStockQueryStepExecutor
from core.blueprint.astock.step_model import AStockQueryStepModel
from core.blueprint.llm_provider import LLMProvider
from core.planner.message import send_message
from core.utils.code_tools import code_tools
from .stock_data_provider import StockDataProvider


class AStockQueryInfoGenerator(StepInfoGenerator):
    def __init__(self):
        self.llm_provider = LLMProvider()
        self.llm_client = self.llm_provider.new_llm_client()
        self.stock_data_provider = StockDataProvider(self.llm_client)
        code_tools.add_with_recover("llm_client",self.llm_client)
        code_tools.add_with_recover("stock_data_provider",self.stock_data_provider)
        

    @property
    def step_description(self) -> str:
        return "提供自然语言A股查询的步骤。比如可以根据热榜推荐股票。"
    
    @property
    def step_model(self) -> Type[BaseStepModel]:
        return AStockQueryStepModel

    @property
    def step_code_generator(self) -> Type["StepCodeGenerator"]:
        return AStockQueryStepCodeGenerator
    
    @property
    def step_executor(self) -> Type["StepExecutor"]:
        return AStockQueryStepExecutor
    
    def get_step_model(self) -> BaseStepModel:
        return AStockQueryStepModel()

    def gen_step_info(self, step_info :dict, query:str)-> Generator[Dict[str, Any], None, AStockQueryStepModel]:
        step = AStockQueryStepModel()
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