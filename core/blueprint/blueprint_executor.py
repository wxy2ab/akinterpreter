

from typing import Dict, Generator
from core.blueprint._base_step_model import BaseStepModel
from core.blueprint._step_abstract import StepExecutor
from core.blueprint.step_data import StepData
from core.blueprint.step_info_provider import StepInfoProvider
from core.blueprint.step_model_collection import StepModelCollection


class BluePrintExecutor:
    def __init__(self,blueprint:StepModelCollection,step_data:StepData):
        self.blueprint = blueprint
        self.step_data = step_data
        self.step_info_provider = StepInfoProvider()
        self.generator_dict:Dict[int,StepExecutor]={}
    
    def excute_step(self,step_info:BaseStepModel)-> Generator[str, None, None]:
        step_number = step_info.step_number
        if step_number not in self.generator_dict:
            info_generator =self.step_info_provider.select_generator(step_info.type)
            step_executor_class = info_generator.step_executor
            step_executor=step_executor_class(step_info,self.step_data)
            self.generator_dict[step_number] = step_executor
        executor = self.generator_dict[step_number]
        yield from executor.execute_step_code()
    
    