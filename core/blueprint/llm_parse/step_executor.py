





from core.blueprint._step_abstract import StepExecutor
from core.blueprint.llm_parse.step_model import LLMParseStepModel
from core.blueprint.step_data import StepData


class LLMParseStepExecutor(StepExecutor):
    def __init__(self, step_info: LLMParseStepModel, step_data: StepData):
        super().__init__(step_info, step_data)