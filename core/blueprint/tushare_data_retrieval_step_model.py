

from typing import Literal

from pydantic import Field
from ._base_step_model import BaseStepModel
from .data_retrieval_step_model import DataRetrievalStepModel

class TushareDataRetrievalStepModel(DataRetrievalStepModel):
    library: Literal['tushare'] = 'tushare'
    step_type: Literal['tushare_data_retrieval'] = 'tushare_data_retrieval'
