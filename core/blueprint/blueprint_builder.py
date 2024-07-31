

from typing import Any, Dict, Generator

from ._step_abstract import StepInfoGenerator

from .llm_provider import LLMProvider

from .step_model_collection import StepModelCollection
from .step_info_provider import StepInfoProvider
from .llm_tools import LLMTools

class BluePrintBuilder:
    def __init__(self):
        self.llm_provider = LLMProvider()
        self.provider = StepInfoProvider() 
        self.blueprint=StepModelCollection()
        self.llm_tools = LLMTools()
        self.llm_client = self.llm_provider.new_llm_client()
        self.max_retry = 3

    def build_blueprint(self, query: str) -> Generator[Dict[str, Any], None, None]:
        prompt = self.provider.get_build_prompt(query)
        self.blueprint.current_query = query

        generator = self.llm_client.one_chat(prompt,is_stream=True)
        plan_text = ""
        for chunk in generator:
            plan_text += chunk
            yield {"type": "plan", "content": chunk}
        steps = self.llm_tools.extract_json_from_text(plan_text)
        retried = 0
        build_success = False
        while True:
            if retried >= self.max_retry:
                break
            try:
                yield from self.generate_steps(query,steps)
                build_success = True
                break
            except Exception as e:
                retried += 1
                yield {"type": "error", "content": str(e)}
        if not build_success:
            yield {"type": "plan", "content": "多次生成计划失败，当前代码无法完成query"}
            raise Exception("多次生成计划失败，当前代码无法完成query")
            
    
    def generate_steps(self,query:str,steps:dict)-> Generator[Dict[str, Any], None, None]:
        generate_error = ""
        for step in steps:
            step_type = step["step_type"]
            generator:StepInfoGenerator = self.provider.select_generator(step_type)
            generate_error , vaild = generator.validate_step_info(step)
            if not vaild:
                yield {"type": "error", "content": generate_error}
                break
            result = yield from generator.gen_step_info(step,query)
            self.blueprint.add_step(result)
        if generate_error:
            raise Exception(generate_error)

    def fix_blueprint(self,query:str,steps :dict, error_msg: str) -> Generator[Dict[str, Any], None, None]:
        prompt = self.provider.get_fix_prompt(query,steps,error_msg)
        generator = self.llm_client.one_chat(prompt,is_stream=True)
        pass
            

        
    def modify_blueprint(self, query: str) -> Generator[Dict[str, Any], None, None]:
        pass