from typing import Generator, Dict, Any
from ._step_abstract import StepCodeGenerator, BaseStepModel
from .akshare_data_retrieval_step_model import AkShareDataRetrievalStepModel

class AkshareDataRetrievalStepCodeGenerator(StepCodeGenerator):
    def gen_step_code(self, step_data: AkShareDataRetrievalStepModel, query: str) -> Generator[Dict[str, Any], None, None]:
        pass

    def fix_code(self, step_data: AkShareDataRetrievalStepModel, code: str, error_info: str) -> Generator[str, None, None]:
        pass