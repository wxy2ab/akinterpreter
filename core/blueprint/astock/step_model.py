


from typing import ClassVar, Literal
from core.blueprint._base_step_model import BaseStepModel


class AStockQueryStepModel(BaseStepModel):
        step_type: ClassVar[Literal['astock_query']] =  'astock_query'