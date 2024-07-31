from .step_model_collection import StepModelCollection
from ._base_step_model import StepModel
from typing import Generator, Dict, Any

class BluePrintCoder:
    def __init__(self,blueprint:StepModelCollection):
        self.blueprint = blueprint
    
    def generate_code(self,step_info:StepModel)-> Generator[Dict[str, Any], None, None]:
        pass