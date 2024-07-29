


from .base_step_model_collection import BaseStepModelCollection


class StepModelCollection(BaseStepModelCollection):
    current_query: str
    query_list: list[str]
    query_summary: str