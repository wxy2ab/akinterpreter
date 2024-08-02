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
        self._blueprint = StepModelCollection()
        self.llm_tools = LLMTools()
        self.llm_client = self.llm_provider.new_llm_client()
        self.last_step_dict = None
        self.max_retry = 3

    @property
    def blueprint(self) -> StepModelCollection:
        return self._blueprint
    
    @blueprint.setter
    def blueprint(self, value: StepModelCollection):
        self._blueprint = value

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
                self._blueprint.clear()
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
        self._blueprint.current_query = query
        self._blueprint.query_summary = query
        prompt = self.provider.get_build_prompt(query)
        plan_text = yield from self._stream_plan(prompt)
        steps = self._parse_plan(plan_text)
        yield from self._execute_plan(query, steps)

    def modify_blueprint(self, query: str) -> Generator[Dict[str, Any], None, None]:
        if self.last_step_dict is None:
            raise ValueError("No existing blueprint to modify")
        self._blueprint.query_list.append(query)
        self._blueprint.current_query = query
        self._blueprint.query_summary = query
        self._blueprint.query_list.append(query)
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
            self._blueprint.add_step(result)

    def fix_blueprint(self, query: str, steps: List[Dict[str, Any]], error_msg: str) -> Generator[Dict[str, Any], None, None]:
        self._blueprint.clear()
        prompt = self.provider.get_fix_prompt(query, steps, error_msg)
        steps = yield from self._generate_plan(prompt)
        yield {"type": "plan", "content": "data: [Done]", "data": steps}
    
    def _make_query_summary(self) -> Generator[Dict[str, Any], None, None]:
        history = self._blueprint.query_list
        current_query = self._blueprint.current_query

        # Step 1: Use LLM API to determine if current_query is consistent with history
        consistency_prompt = f"请比较以下当前查询与查询历史。判断主题是否发生了变化。请回答'改变'或'一致'。\n\n当前查询: {current_query}\n\n查询历史: {history}"
        
        consistency_response = yield from self._stream_plan(consistency_prompt)
        is_topic_changed = '改变' in consistency_response

        if is_topic_changed:
            # If the topic has changed, reset the query list and summary
            self._blueprint.query_list = [current_query]
            self._blueprint.query_summary = current_query
            yield {"type": "message", "content": "主题已改变。查询列表和摘要已重置。"}
        else:
            # If the topic hasn't changed, summarize the current query and history
            summary_prompt = f"请将以下查询概括为一个简洁的陈述，以捕捉整体意图：\n\n查询历史: {history}\n当前查询: {current_query}"
            
            summary_response = yield from self._stream_plan(summary_prompt)
            
            self._blueprint.query_summary = summary_response.strip()
            self._blueprint.query_list.append(current_query)
            yield {"type": "message", "content": f"更新后的摘要: {self._blueprint.query_summary}"}

    def clear(self):
        self._blueprint = StepModelCollection()
        self.last_step_dict = None