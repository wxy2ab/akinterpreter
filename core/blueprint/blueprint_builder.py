

from typing import Any, Dict, Generator

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

    def build_blueprint(self, query: str) -> Generator[Dict[str, Any], None, None]:
        prompt = self.provider.get_build_prompt(query)
        generator = self.llm_client.one_chat(prompt,is_stream=True)
        plan_text = ""
        for chunk in generator:
            plan_text += chunk
            yield {"type": "plan", "content": chunk}
        steps = self.llm_tools.extract_json_from_text(plan_text)
        
    def modify_blueprint(self, query: str) -> Generator[Dict[str, Any], None, None]:
        pass