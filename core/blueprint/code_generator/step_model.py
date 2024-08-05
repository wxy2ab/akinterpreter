


from typing import ClassVar, Literal
from core.blueprint._base_step_model import BaseStepModel


class CodeGenStepModel(BaseStepModel):
        step_type: ClassVar[Literal['function_generate']] =  'function_generate'