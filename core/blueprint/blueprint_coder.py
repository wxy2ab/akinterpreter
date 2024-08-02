from ._step_abstract import StepCodeGenerator, StepInfoGenerator
from .step_data import StepData
from .step_info_provider import StepInfoProvider
from .step_model_collection import StepModelCollection
from ._base_step_model import BaseStepModel
from typing import Generator, Dict, Any

class BluePrintCoder:
    def __init__(self,blueprint:StepModelCollection,step_data:StepData):
        self.blueprint = blueprint
        self.step_data = step_data
        self.step_info_provider = StepInfoProvider()
        self.generator_dict:Dict[int,StepCodeGenerator]={}
    
    def generate_step(self,step_info:BaseStepModel)->Generator[Dict[str,Any],None,None]:
        step_number = step_info.step_number
        if step_number not in self.generator_dict:
            info_generator =self.step_info_provider.select_generator(step_info.type)
            #info_generator.step_code_generator(step_info,self.step_data)
            code_generator_class = info_generator.step_code_generator
            code_generator = code_generator_class(step_info,self.step_data)
            self._code_generator = code_generator
            self.generator_dict[step_number] = code_generator
        code_generator = self.generator_dict[step_number]
        yield from code_generator.pre_enhancement()
        yield from code_generator.gen_step_code()
        yield from code_generator.post_enhancement()
        code_generator.make_step_sure()



    def generate_code(self)-> Generator[Dict[str, Any], None, None]:
        for step in self.blueprint:
            yield from self.generate_step(step)


    def modify_step_code(self, step_number: int, query: str) -> Generator[Dict[str, Any], None, None]:
        step = self.blueprint[step_number]
        if step is None:
            raise Exception(f"步骤{step_number}不存在")
        code_generator = None
        if step_number in self.generator_dict:
            code_generator = self.generator_dict[step_number]
        else:
            info_generator = self.step_info_provider.select_generator(step.type)
            code_generator_class = info_generator.step_code_generator
            code_generator = code_generator_class(step, self.step_data)
            self.generator_dict[step_number] = code_generator
        
        yield from code_generator.modify_step_code(step_number, query)
        
        