from typing import Any, Dict, Generator, Type

from ._base_step_model import BaseStepModel
from .akshare_data_retrieval_step_model import AkShareDataRetrievalStepModel
from .llm_provider import LLMProvider
from ._step_abstract import StepInfoGenerator
from .akshare_data_retrieval_step_model import AkShareDataRetrievalStepModel
from ..rag.akshare_functions import AkshareFunctions
from ..planner.message import send_message


class AkShareDataRetrievalStepInfoGenerator(StepInfoGenerator):
    def __init__(self) -> None:
        self.retrieval = AkshareFunctions()
        self.llm_provider = LLMProvider()
        self.llm_client = self.llm_provider.new_llm_client()

    @property
    def step_description(self) -> str:
        return "提供数据查询步骤，目的是获取数据。可以提供股票数据,期货数据,期权数据,债券数据,外汇数据,宏观经济数据,基金数据,指数数据,另类数据,新闻数据,港股数据,美股数据,金融工具,数据工具,行业数据,公司数据,交易所数据,市场情绪数据等财经方面的资讯和数据"
    
    @property
    def step_model(self) -> Type[BaseStepModel]:
        return AkShareDataRetrievalStepModel
    
    def get_step_model(self) -> BaseStepModel:
        return AkShareDataRetrievalStepModel()

    def gen_step_info(self, step_info:dict, query:str)-> Generator[Dict[str, Any], None, AkShareDataRetrievalStepModel]:
        step = AkShareDataRetrievalStepModel()
        step.description = step_info["task"]
        step.save_data_to=step_info["save_data_to"]
        step.required_data=step_info["required_data"]
        yield send_message(type="plan",content="生成任务\n")
        new_description = ""
        generator =  self.gen_new_description(step_info)
        for chunk in generator:
            new_description += chunk
            yield send_message(type="plan",content=chunk)
        step.description = new_description
        yield send_message(type="plan",content="获取可用函数\n")
        selected_functions = self.retrieval.get_functions(query,is_stream=False)
        step.selected_functions = selected_functions
        yield send_message(type="plan",content="完成步骤\n")
        return step

    def validate_step_info(self, step_data) -> Generator[Dict[str, Any], None, None]:
        pass

    def fix_step_info(self, step_data, query, error_msg) -> Generator[Dict[str, Any], None, None]:
        pass

    def gen_new_description(self, step_data) -> Generator[Dict[str, Any], None, str]:
        # 获取初始任务描述
        description = step_data.get("task", "")
        save_data_to = step_data.get("save_data_to", "")
        required_data = step_data.get("required_data", [])

        # 准备提示词
        prompt = f"任务: {description}\n需要的变量: {required_data}\n将数据保存到: {save_data_to}\n请优化这段任务描述，使其更清晰并更有助于代码生成。"

        # 使用llm_client生成优化后的描述
        optimized_description = yield from self.llm_client.one_chat(prompt, is_stream=True)

        return optimized_description