





from core.blueprint._step_abstract import StepExecutor
from core.blueprint.astock.step_model import AStockQueryStepModel
from core.blueprint.step_data import StepData


class AStockQueryStepExecutor(StepExecutor):
    def __init__(self, step_info: AStockQueryStepModel, step_data: StepData):
        super().__init__(step_info, step_data)