from typing import ClassVar, Literal
from core.blueprint._base_step_model import BaseStepModel


class DbQueryStepModel(BaseStepModel):
        step_type: ClassVar[Literal['dbquery']] =  'dbquery'