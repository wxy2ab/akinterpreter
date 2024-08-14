




import json
from typing import Any, Dict, Generator
from tenacity import retry, retry_if_exception, stop_after_attempt
from core.blueprint._step_abstract import StepCodeGenerator
from core.blueprint.astock.step_model import AStockQueryStepModel
from core.blueprint.llm_provider import LLMProvider
from core.blueprint.llm_tools import LLMTools
from core.blueprint.step_data import StepData
from core.planner.code_enhancement_system import CodeEnhancementSystem
from core.planner.message import send_message
from core.utils.code_tools import code_tools
from .stock_query_stream import StockQueryStream
from .stock_data_provider import StockDataProvider


class AStockQueryStepCodeGenerator(StepCodeGenerator):
    def __init__(self,step_info: AStockQueryStepModel,step_data:StepData):
        self.step_info = step_info
        self.step_data = step_data
        self._step_code = ""
        self.llm_provider = LLMProvider()
        self.llm_tools = LLMTools()
        self.code_enhancement_system = CodeEnhancementSystem()
        self.llm_client = self.llm_provider.new_llm_client()
        self.stock_data_provider =StockDataProvider(self.llm_client)
        self.stock_query_stream = StockQueryStream(self.llm_client,self.stock_data_provider)
        self._prompt=""

    def make_step_sure(self):
        step_number = self.step_info.step_number
        self.step_data.set_step_code(step_number, self._step_code)
        
    @property
    def step_code(self) -> str:
        return self._step_code


    @retry(stop=stop_after_attempt(3), retry=retry_if_exception(False))
    def gen_step_code(self) -> Generator[Dict[str, Any], None, None]:
        description = self.step_info.description
        required_data_list = self.step_info.required_data
        save_data_to = self.step_info.save_data_to

        generated_code=""
        prompt = ""

        generator = self.stock_query_stream.generate_code(description)
        for chunk in generator:
            if chunk["type"] == "message" and "data: [Done]" in chunk["content"]:
                generated_code =chunk["code"]
                prompt = chunk["prompt"]
            else:
                yield chunk

        self._prompt = prompt
        self._step_code = generated_code
        yield send_message("代码生成成功。", "success")
    
    def fix_code(self, error: str) -> Generator[str, None, None]:
        generator = self.stock_query_stream._fix_runtime_error(self._step_code,error=error,prompt=self._prompt)
        for chunk in generator:
            if chunk["type"] == "message" and "data: [Done]" in chunk["content"]:
                self._step_code =chunk["code"]
            else:
                yield chunk

    