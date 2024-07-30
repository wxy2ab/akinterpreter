from typing import Literal

from pydantic import Field
from ._base_step_model import BaseStepModel


class DataRetrievalStepModel(BaseStepModel):
    step_type: Literal['data_retrieval'] = 'data_retrieval'
    selected_functions: list[str] = Field(default_factory=list)
