from typing import Literal, Dict, Any, List, ClassVar
from pydantic import Field
from ._base_step_model import BaseStepModel

class DataAnalysisStepModel(BaseStepModel):
    step_type: ClassVar[Literal['data_analysis']] =  Field('data_analysis', allow_mutation=False)
    
    data_requirements: List[str] = Field(default_factory=list)

    @property
    def analysis_result(self) -> str:
        return f"analysis_result_{self.step_number}"

    def to_dict(self) -> Dict[str, Any]:
        base_dict = super().to_dict()
        base_dict.update({
            "data_requirements": self.data_requirements,
            "analysis_result": self.analysis_result
        })
        return base_dict

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DataAnalysisStepModel':
        # Remove 'analysis_result' from the data if present, as it's a computed property
        data.pop('analysis_result', None)
        return cls(**data)