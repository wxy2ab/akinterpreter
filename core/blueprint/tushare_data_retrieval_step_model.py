

from typing import ClassVar, Literal, Optional

from pydantic import Field
from ._base_step_model import BaseStepModel
from .data_retrieval_step_model import DataRetrievalStepModel

class TushareDataRetrievalStepModel(DataRetrievalStepModel):
    library: Literal['tushare'] = 'tushare'
    step_type:  ClassVar[str] = 'tushare_data_retrieval'
