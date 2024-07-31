

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

    @property
    @abstractmethod
    def step_code_generator(self) -> Type["StepCodeGenerator"]:
        pass

    @abstractmethod
    def get_step_model(self) -> BaseStepModel:
        pass

    @abstractmethod
    def gen_step_info(self, step_info :dict , query: str ) -> Generator[Dict[str, Any], None, BaseStepModel]:
        pass

    @abstractmethod
    def validate_step_info(self, step_info: dict) -> tuple[str, bool]:
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

class StepReport(ABC):
    @abstractmethod
    def gen_report(self, step_data: BaseStepModel, step_result: StepResult) -> Generator[Dict[str, Any], None, None]:
        pass
