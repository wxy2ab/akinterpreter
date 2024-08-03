

from typing import Literal

from pydantic import Field
from ._base_step_model import BaseStepModel
from .data_retrieval_step_model import DataRetrievalStepModel

class TushareDataRetrievalStepModel(DataRetrievalStepModel):
    library: Literal['akshare'] = 'tushare'
    step_type: Literal['data_retrieval'] = 'tushare_data_retrieval'
    selected_functions: list[str] = Field(default_factory=list)
