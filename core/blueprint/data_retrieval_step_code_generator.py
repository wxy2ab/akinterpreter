from typing import Generator, Dict, Any
# 修复：导入BaseStepModel类
from._step_abstract import StepCodeGenerator, BaseStepModel

class DataRetrievalStepCodeGenerator(StepCodeGenerator):
    def gen_step_code(self, step_data: BaseStepModel, query: str) -> Generator[Dict[str, Any], None, None]:
        pass

    def fix_code(self, step_data: BaseStepModel, code: str, error_info: str) -> Generator[str, None, None]:
        pass