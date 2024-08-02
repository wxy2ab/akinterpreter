

from abc import ABC, abstractmethod
from typing import ClassVar, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic import BaseModel
from typing import Type, Dict, Any

class BaseStepModel(BaseModel):
    step_number: int = -1
    description: str = ""
    save_data_to: list[str] =  Field(default_factory=list)
    required_data: list[str] = Field(default_factory=list)
    type: str = Field(default="")  

    # 类变量，子类必须覆盖这个值
    step_type: ClassVar[str]

    def __init__(self, **data):
        super().__init__(**data)
        self.type = self.step_type 

    @field_validator('type', mode='before')
    @classmethod
    def set_type(cls, v):
        if not hasattr(cls, 'step_type'):
            raise ValueError(f"step_type must be defined for {cls.__name__}")
        return cls.step_type

    def model_dump(self, *args, **kwargs) -> Dict[str, Any]:
        return super().model_dump(*args, **kwargs)

    @classmethod
    def model_validate(cls, obj: Any) -> 'BaseStepModel':
        return super().model_validate(obj)

    def model_dump_json(self, *args, **kwargs) -> str:
        return super().model_dump_json(*args, **kwargs)

    @classmethod
    def model_validate_json(cls, json_data: str) -> 'BaseStepModel':
        return super().model_validate_json(json_data)

    # def to_dict(self) -> Dict[str, Any]:
    #     return self.model_dump(exclude={'step_type'})

    # @classmethod
    # def from_dict(cls, data: Dict[str, Any]) -> 'BaseStepModel':
    #     return cls.model_validate(data)
    
    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={
            ClassVar: lambda v: str(v),
        }
    )

class StepModelTools:

    @staticmethod
    def get_model_structure(model: Type[BaseModel]) -> Dict[str, Any]:
        structure = {}
        for name, field in model.model_fields.items():
            if name == 'type' and field.init is False:
                continue  # Skip 'type' field as it's set automatically
            field_info = {
                "type": str(field.annotation),
                "required": field.is_required(),
            }
            if field.description:
                field_info["description"] = field.description
            if field.default is not None:
                field_info["default"] = str(field.default)
            structure[name] = field_info
        
        # Add information about step_type
        if hasattr(model, 'step_type'):
            structure['step_type'] = {"value": model.step_type, "note": "This is a fixed value for this model"}
        
        return structure
    
    @staticmethod
    def format_model_structure(structure: Dict[str, Any]) -> str:
        formatted = "数据结构:\n"
        for field, info in structure.items():
            formatted += f"- {field}:\n"
            for key, value in info.items():
                formatted += f"    {key}: {value}\n"
            formatted += "\n"
        return formatted
