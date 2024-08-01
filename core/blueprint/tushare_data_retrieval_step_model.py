

from typing import Literal

from pydantic import Field
from ._base_step_model import BaseStepModel
from .data_retrieval_step_model import DataRetrievalStepModel

class AkShareDataRetrievalStepModel(DataRetrievalStepModel):
    library: Literal['akshare'] = 'akshare'
    step_type: Literal['data_retrieval'] = 'akshare_data_retrieval'
