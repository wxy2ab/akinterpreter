


from pydantic import Field
from typing import List
from .base_step_model_collection import BaseStepModelCollection


class StepModelCollection(BaseStepModelCollection):
    current_query: str = ""
    query_list: list[str] = Field(default_factory=list)
    query_summary: str = ""