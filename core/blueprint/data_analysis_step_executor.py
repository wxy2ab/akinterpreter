from .data_analysis_step_model import DataAnalysisStepModel
from .step_data import StepData
from ._step_abstract import StepExecutor

class DataAnalysisStepExecutor(StepExecutor):
    def __init__(self, step_info: DataAnalysisStepModel, step_data: StepData):
        super().__init__(step_info, step_data)