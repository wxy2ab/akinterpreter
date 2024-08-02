from typing import Literal, Dict, Any, List, ClassVar
from pydantic import Field
from ._base_step_model import BaseStepModel

class DataRetrievalStepModel(BaseStepModel):
    step_type: ClassVar[Literal['data_retrieval']] = Field('data_retrieval', allow_mutation=False) 
    selected_functions: List[str] = Field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_number": self.step_number,
            "description": self.description,
            "save_data_to": self.save_data_to,
            "required_data": self.required_data,
            "type": self.type,
            "selected_functions": self.selected_functions
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DataRetrievalStepModel':
        return cls(
            step_number=data.get('step_number'),
            description=data.get('description', ''),
            save_data_to=data.get('save_data_to', []),
            required_data=data.get('required_data', []),
            selected_functions=data.get('selected_functions', [])
        )