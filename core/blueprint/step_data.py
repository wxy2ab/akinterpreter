


from typing import Any, Dict
from .llm_provider import LLMProvider

class StepData:
    def __init__(self):
        self._global_vars = Dict[str, Any]
        self._step_vars = Dict[int, Dict[str, Any]]
        self._step_codes = Dict[int, str]
        self.llm_provider = LLMProvider()

    @property
    def global_vars(self):
        return self._global_vars
    
    @property
    def step_vars(self):
        return self._step_vars
    
    @property
    def step_codes(self):
        return self._step_codes
    
    def set_step_code(self, step_id: int, code: str):
        if step_id<=0:
            raise ValueError("step_id must be greater than 0")
        self._step_codes[step_id] = code

    def __getitem__(self, index: int) -> Dict[str, Any]:
        if index <= 0:
            raise ValueError("Index must be greater than 0")
        if index not in self._step_vars:
            self._step_vars[index] = {}
        return self._step_vars[index]

    def __setitem__(self, index: int, value: Dict[str, Any]) -> None:
        if index <= 0:
            raise ValueError("Index must be greater than 0")
        if not isinstance(value, dict):
            raise TypeError("Value must be a dictionary")
        self._step_vars[index] = value

    def __len__(self) -> int:
        return len(self._step_vars)

    def __iter__(self):
        return iter(self._step_vars)

    def __contains__(self, index: int) -> bool:
        return index in self._step_vars