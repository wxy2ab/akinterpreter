from typing import Generator
from .step_data import StepData
from .blueprint_builder import BluePrintBuilder
from .blueprint_coder import BluePrintCoder
from .blueprint_executor import BluePrintExecutor
from .blueprint_reporter import BluePrintReporter
from .step_model_collection import StepModelCollection

class BluePrint:
    def __init__(self):
        self.blueprint_builder = BluePrintBuilder()
        self.blueprint_coder = None
        self.blueprint_executor =None
        self.blueprint_reporter = None
        self.blueprint =None
        self.max_retry = 3
        self.step_data = StepData()
    
    def build_blueprint(self,query:str)->Generator[dict[str,any],None,None]:
        yield from self.blueprint_builder.build_blueprint(query)
        self.blueprint = self.blueprint_builder.blueprint

    def modify_blueprint(self,query:str,steps:dict[str,any])->Generator[dict[str,any],None,None]:
        yield from self.blueprint_builder.modify_blueprint(query)
        self.blueprint = self.blueprint_builder.blueprint
    
    def generate_code(self,step_info:dict[str,any])->Generator[dict[str,any],None,None]:
        self.blueprint_coder = BluePrintCoder(self.blueprint)
        yield from self.blueprint_coder.generate_code(step_info)