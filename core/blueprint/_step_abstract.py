

from abc import ABC, abstractmethod
from typing import Any, Dict, Generator, Type
from ._base_step_model import BaseStepModel
from .step_result import StepResult

class StepInfoGenerator(ABC):
    @property
    @abstractmethod
    def step_description(self) -> str:
        pass
    
    @property
    @abstractmethod
    def step_model(self) -> Type[BaseStepModel]:
        pass

    @abstractmethod
    def gen_step_info(self, step_data_type: Type[BaseStepModel], query: str) -> Generator[Dict[str, Any], None, None]:
        pass

    @abstractmethod
    def validate_step_info(self, step_data: BaseStepModel) -> tuple[str, bool]:
        pass

    @abstractmethod
    def fix_step_info(self, step_data: BaseStepModel, query: str, error_msg: str) -> Generator[Dict[str, Any], None, None]:
        pass

class StepCodeGenerator(ABC):
    @abstractmethod
    def gen_step_code(self, step_data: BaseStepModel, query: str) -> Generator[Dict[str, Any], None, None]:
        pass

    @abstractmethod
    def fix_code(self, step_data: BaseStepModel, code: str, error_info: str) -> Generator[str, None, None]:
        pass

    @abstractmethod
    def pre_enhancement(self, step_data: BaseStepModel, enhance_prompt: str) -> Generator[str, None, None]:
        pass

    @abstractmethod
    def post_enhancement(self, step_data: BaseStepModel, code: str, enhance_prompt: str) -> Generator[str, None, None]:
        pass

class StepExecutor(ABC):
    @abstractmethod
    def execute_step_code(self, step_data: BaseStepModel, code: str, global_vars: Dict[str, Any]) -> Generator[Dict[str, Any], None, None]:
        pass

    @abstractmethod
    def redo_step(self, step_data: BaseStepModel, step_result: StepResult) -> Generator[Dict[str, Any], None, None]:
        pass

