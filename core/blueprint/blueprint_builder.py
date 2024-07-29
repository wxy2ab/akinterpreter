

from typing import Any, Dict, Generator

from .step_model_collection import StepModelCollection
from .step_info_provider import StepInfoProvider


class BluePrintBuilder:
    def __init__(self):
        self.provider = StepInfoProvider() 
        self.blueprint=StepModelCollection()
    
    def build_blueprint(self, query: str) -> Generator[Dict[str, Any], None, None]:
        pass
    def modify_blueprint(self, query: str) -> Generator[Dict[str, Any], None, None]:
        pass