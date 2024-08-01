from typing import Any, Dict, Generator, List

from ._step_abstract import StepInfoGenerator
from .llm_provider import LLMProvider
from .step_model_collection import StepModelCollection
from .step_info_provider import StepInfoProvider
from .llm_tools import LLMTools

class BluePrintBuilder:
    def __init__(self):
        self.llm_provider = LLMProvider()
        self.provider = StepInfoProvider() 
        self.blueprint = StepModelCollection()
        self.llm_tools = LLMTools()
        self.llm_client = self.llm_provider.new_llm_client()
        self.last_step_dict = None
        self.max_retry = 3

    def _stream_plan(self, prompt: str) -> Generator[Dict[str, Any], None, str]:
        generator = self.llm_client.one_chat(prompt, is_stream=True)
        plan_text = ""
        for chunk in generator:
            plan_text += chunk
            yield {"type": "plan", "content": chunk}
        return plan_text

    def _parse_plan(self, plan_text: str) -> List[Dict[str, Any]]:
        return self.llm_tools.extract_json_from_text(plan_text)

    def _execute_plan(self, query: str, steps: List[Dict[str, Any]]) -> Generator[Dict[str, Any], None, None]:
        retried = 0
        success = False
        while retried < self.max_retry:
            try:
                self.blueprint.clear()
                yield from self.generate_steps(query, steps)
                self.last_step_dict = steps
                success = True
                break
            except Exception as e:
                retried += 1
                yield {"type": "error", "content": str(e)}
                if retried < self.max_retry:
                    generator = self.fix_blueprint(query, steps, str(e))
                    for chunk in generator:
                        if chunk["type"] == "plan" and chunk.get("data"):
                            steps = chunk["data"]
                        yield chunk
        
        if not success:
            error_msg = f"多次{'生成' if self.last_step_dict is None else '修改'}计划失败，无法完成query"
            yield {"type": "plan", "content": error_msg}
            raise Exception(error_msg)

    def build_blueprint(self, query: str) -> Generator[Dict[str, Any], None, None]:
        self.blueprint.current_query = query
        prompt = self.provider.get_build_prompt(query)
        plan_text = yield from self._stream_plan(prompt)
        steps = self._parse_plan(plan_text)
        yield from self._execute_plan(query, steps)

    def modify_blueprint(self, query: str) -> Generator[Dict[str, Any], None, None]:
        if self.last_step_dict is None:
            raise ValueError("No existing blueprint to modify")
        
        self.blueprint.current_query = query
        prompt = self.provider.get_modify_prompt(query, self.last_step_dict)
        plan_text = yield from self._stream_plan(prompt)
        steps = self._parse_plan(plan_text)
        yield from self._execute_plan(query, steps)

    def generate_steps(self, query: str, steps: List[Dict[str, Any]]) -> Generator[Dict[str, Any], None, None]:
        for step in steps:
            step_type = step["step_type"]
            generator: StepInfoGenerator = self.provider.select_generator(step_type)
            generate_error, valid = generator.validate_step_info(step)
            if not valid:
                yield {"type": "error", "content": generate_error}
                raise ValueError(generate_error)
            result = yield from generator.gen_step_info(step, query)
            self.blueprint.add_step(result)

    def fix_blueprint(self, query: str, steps: List[Dict[str, Any]], error_msg: str) -> Generator[Dict[str, Any], None, None]:
        self.blueprint.clear()
        prompt = self.provider.get_fix_prompt(query, steps, error_msg)
        steps = yield from self._generate_plan(prompt)
        yield {"type": "plan", "content": "data: [Done]", "data": steps}