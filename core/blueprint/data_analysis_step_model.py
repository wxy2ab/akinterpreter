
from typing import Literal

from pydantic import Field
from ._base_step_model import BaseStepModel


class DataAnalysisStepModel(BaseStepModel):
    step_type:Literal['data_analysis'] = 'data_analysis'
    data_requirements:list[str] = Field(default_factory=list)