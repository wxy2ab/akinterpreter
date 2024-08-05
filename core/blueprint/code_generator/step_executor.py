





from core.blueprint._step_abstract import StepExecutor
from core.blueprint.code_generator.step_model import CodeGenStepModel
from core.blueprint.step_data import StepData


class CodeGenStepExecutor(StepExecutor):
    def __init__(self, step_info: CodeGenStepModel, step_data: StepData):
        super().__init__(step_info, step_data)