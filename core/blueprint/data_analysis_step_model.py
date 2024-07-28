
from typing import Literal
from ._base_step_model import BaseStepModel


class DataAnalysisStepModel(BaseStepModel):
    step_type:Literal['data_analysis'] = 'data_analysis'