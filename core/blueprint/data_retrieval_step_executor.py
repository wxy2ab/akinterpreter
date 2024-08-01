from .step_data import StepData
from .data_retrieval_step_model import DataRetrievalStepModel
from ._step_abstract import StepExecutor


class DataRetrievalStepExecutor(StepExecutor):
    def  __init__(self,step_info: DataRetrievalStepModel,step_data:StepData):
        super().__init__(step_info,step_data)