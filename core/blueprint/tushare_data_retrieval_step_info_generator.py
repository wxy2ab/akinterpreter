from ..rag.akshare_functions import AkshareFunctions
from ._step_abstract import StepInfoGenerator
from .llm_provider import LLMProvider


class TushareDataRetrievalStepInfoGenerator(StepInfoGenerator):
    def __init__(self) -> None:
        self.retrieval = AkshareFunctions()
        self.llm_provider = LLMProvider()
        self.llm_client = self.llm_provider.new_llm_client()
        self.llm_cheap_client  = self.llm_provider.new_cheap_client()