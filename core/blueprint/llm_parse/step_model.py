from typing import ClassVar, Literal
from core.blueprint._base_step_model import BaseStepModel


class LLMParseStepModel(BaseStepModel):
        step_type: ClassVar[Literal['llm_parse']] =  'llm_parse'