from ..rag.akshare_functions import AkshareFunctions
from ._step_abstract import StepInfoGenerator,StepCodeGenerator,StepExecutor
from .llm_provider import LLMProvider
from .tushare_data_retrieval_step_model import TushareDataRetrievalStepModel
from typing import Type
from ._base_step_model import BaseStepModel
from .tushare_data_retrieval_step_code_generator import TushareDataRetrievalStepCodeGenerator
from data_retrieval_step_executor import DataRetrievalStepExecutor



class TushareDataRetrievalStepInfoGenerator(StepInfoGenerator):
    def __init__(self) -> None:
        self.retrieval = AkshareFunctions()
        self.llm_provider = LLMProvider()
        self.llm_client = self.llm_provider.new_llm_client()
        self.llm_cheap_client  = self.llm_provider.new_cheap_client()
    
    @property
    def step_description(self) -> str:
        return "Tushare Data Retrieval"
    
    @property
    def step_model(self) -> Type[BaseStepModel]:
        return TushareDataRetrievalStepModel
    
    @property
    def step_code_generator(self) -> Type["StepCodeGenerator"]:
        return TushareDataRetrievalStepCodeGenerator
    
    @property
    def step_executor(self) -> Type["StepExecutor"]:
        return DataRetrievalStepExecutor