from typing import Any, Dict, Literal, ClassVar
from pydantic import Field
from ._base_step_model import BaseStepModel
from .data_retrieval_step_model import DataRetrievalStepModel

class AkShareDataRetrievalStepModel(DataRetrievalStepModel):
    library: Literal['akshare'] = 'akshare'
    step_type: ClassVar[Literal['akshare_data_retrieval']] = Field('akshare_data_retrieval', allow_mutation=False)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "library": self.library,
            "step_type": self.step_type,
            "step_number": self.step_number,
            "description": self.description,
            "save_data_to": self.save_data_to,
            "required_data": self.required_data,
            "selected_functions": self.selected_functions
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AkShareDataRetrievalStepModel':
        return cls(
            library=data.get('library', 'akshare'),
            step_number=data.get('step_number'),
            description=data.get('description', ''),
            save_data_to=data.get('save_data_to', []),
            required_data=data.get('required_data', []),
            selected_functions=data.get('selected_functions', [])
        )