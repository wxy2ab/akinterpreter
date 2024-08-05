




from .data_export_step_model import DataExportStepModel
from .step_data import StepData
from ._step_abstract import StepExecutor


class DataExportStepExecutor(StepExecutor):
    def __init__(self, step_info: DataExportStepModel, step_data: StepData):
        super().__init__(step_info, step_data)
