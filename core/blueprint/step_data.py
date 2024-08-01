from typing import Any, Dict
from .llm_provider import LLMProvider
from core.utils.code_tools import code_tools

# 初始化这个类会导致code_tools 清空，所以同一时间，只能有一个StepData ,  因为同一时间只允许一个code_tools ,多了就会错误
class StepData:
    def __init__(self):
        self._global_vars: Dict[str, Any] = {}
        self._step_vars: Dict[int, Dict[str, Any]] = {}
        self._step_codes: Dict[int, str] = {}
        self.llm_provider = LLMProvider()
        self._tools = code_tools
        self._tools.clear()
        self.add_default_vars()

    def add_default_vars(self):
        default_vars = {
            "llm_provider": self.llm_provider,
            "llm_client": self.llm_provider.new_llm_client(),
            "llm_factory": self.llm_provider.llm_factory,
            "data_summarizer": self.llm_provider._data_summarizer
        }
        for name, value in default_vars.items():
            if not self._tools.is_exists(name):
                self._tools.add(name, value)
        
    @property
    def global_vars(self):
        return self._global_vars
    
    @property
    def step_vars(self):
        return self._step_vars
    
    @property
    def step_codes(self):
        return self._step_codes
    
    @property
    def tools(self):
        return self._tools
    
    def set_step_code(self, step_id: int, code: str):
        if step_id <= 0:
            raise ValueError("step_id must be greater than 0")
        self._step_codes[step_id] = code

    def set_step_vars(self, step_id: int, step_var: Dict[str, Any]):
        if step_id <= 0:
            raise ValueError("step_id must be greater than 0")
        self._step_vars[step_id] = step_var

    def __getitem__(self, name):
        return self._tools[name]

    def __setitem__(self, name, value):
        self._tools[name] = value

    def __len__(self):
        return len(self._tools)

    def __iter__(self):
        return iter(self._tools)

    def __contains__(self, name):
        return name in self._tools