


from typing import Dict, Any
from ._base_step_model import BaseStepModel

class StepResult:
    def __init__(self, step_data: BaseStepModel):
        self._step_data = step_data
        self._step_code = ""
        self._step_variables: Dict[str, Any] = {}
        self._step_output: Dict[str, Any] = {}

    @property
    def step_data(self) -> BaseStepModel:
        return self._step_data

    @step_data.setter
    def step_data(self, value: BaseStepModel):
        if not isinstance(value, BaseStepModel):
            raise TypeError("step_data must be an instance of BaseStepModel")
        self._step_data = value

    @property
    def step_code(self) -> str:
        return self._step_code

    @step_code.setter
    def step_code(self, value: str):
        if not isinstance(value, str):
            raise TypeError("step_code must be a string")
        self._step_code = value

    @property
    def step_variables(self) -> Dict[str, Any]:
        return self._step_variables

    @step_variables.setter
    def step_variables(self, value: Dict[str, Any]):
        if not isinstance(value, dict):
            raise TypeError("step_variables must be a dictionary")
        self._step_variables = value

    @property
    def step_output(self) -> Dict[str, Any]:
        return self._step_output

    @step_output.setter
    def step_output(self, value: Dict[str, Any]):
        if not isinstance(value, dict):
            raise TypeError("step_output must be a dictionary")
        self._step_output = value