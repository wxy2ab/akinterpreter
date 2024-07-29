

from typing import Literal
from ._base_step_model import BaseStepModel


class AkShareDataRetrievalStepModel(BaseStepModel):
    step_type: Literal['data_retrieval'] = 'data_retrieval'
