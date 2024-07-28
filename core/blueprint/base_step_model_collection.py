from pydantic import BaseModel, Field, field_validator
from typing import Dict, List, Type, Union
from collections import OrderedDict

from ._base_step_model import BaseStepModel

class BaseStepModelCollection(BaseModel):
    steps: Dict[int, BaseStepModel] = Field(default_factory=OrderedDict)

    @field_validator('steps')
    @classmethod
    def validate_step_numbers(cls, v):
        for step_number, step in v.items():
            if step.step_number != step_number:
                raise ValueError(f"Step number mismatch: key {step_number} does not match step.step_number {step.step_number}")
        return v

    def add_step(self, step: BaseStepModel):
        new_step_number = len(self.steps) + 1
        new_step = step.model_copy(update={'step_number': new_step_number})
        self.steps[new_step_number] = new_step

    def insert_step(self, position: int, step: BaseStepModel):
        if position < 1 or position > len(self.steps) + 1:
            raise ValueError(f"Invalid position {position}. Valid range is 1 to {len(self.steps) + 1}")
        
        # Shift existing steps
        new_steps = OrderedDict()
        for i in range(1, position):
            new_steps[i] = self.steps[i]
        
        # Insert new step
        new_steps[position] = step.model_copy(update={'step_number': position})
        
        # Shift and renumber remaining steps
        for i in range(position, len(self.steps) + 1):
            old_step = self.steps[i]
            new_steps[i + 1] = old_step.model_copy(update={'step_number': i + 1})
        
        self.steps = new_steps

    def get_step(self, step_number: int) -> Union[BaseStepModel, None]:
        return self.steps.get(step_number)

    def remove_step(self, step_number: int) -> Union[BaseStepModel, None]:
        if step_number not in self.steps:
            return None
        removed_step = self.steps.pop(step_number)
        self.renumber_steps()
        return removed_step

    def list_steps(self) -> List[BaseStepModel]:
        return list(self.steps.values())

    def get_step_numbers(self) -> List[int]:
        return list(self.steps.keys())

    def get_steps_by_type(self, step_type: str) -> List[BaseStepModel]:
        return [step for step in self.steps.values() if step.type == step_type]

    def clear(self):
        self.steps.clear()

    def __len__(self):
        return len(self.steps)

    def __iter__(self):
        return iter(self.steps.values())

    def __getitem__(self, step_number: int) -> BaseStepModel:
        if step_number not in self.steps:
            raise KeyError(f"Step number {step_number} not found in the collection")
        return self.steps[step_number]

    @classmethod
    def create_from_list(cls, steps: List[BaseStepModel]) -> 'BaseStepModelCollection':
        collection = cls()
        for step in steps:
            collection.add_step(step)
        return collection

    def renumber_steps(self):
        new_steps = OrderedDict()
        for index, (_, step) in enumerate(self.steps.items(), start=1):
            new_steps[index] = step.model_copy(update={'step_number': index})
        self.steps = new_steps