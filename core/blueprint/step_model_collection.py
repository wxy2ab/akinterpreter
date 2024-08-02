
import json
from pydantic import Field
from typing import Any, List,Dict
from .base_step_model_collection import BaseStepModelCollection


class StepModelCollection(BaseStepModelCollection):
    current_query: str = ""
    query_list: list[str] = Field(default_factory=list)
    query_summary: str = ""

    def model_dump(self, **kwargs) -> Dict[str, Any]:
        """自定义序列化方法"""
        base_dump = super().model_dump(**kwargs)
        return {
            **base_dump,
            "current_query": self.current_query,
            "query_list": self.query_list,
            "query_summary": self.query_summary
        }

    @classmethod
    def model_validate(cls, obj: Any) -> 'StepModelCollection':
        """自定义反序列化方法"""
        if isinstance(obj, str):
            obj = json.loads(obj)
        
        base_collection = super().model_validate(obj)
        
        return cls(
            steps=base_collection.steps,
            current_query=obj.get('current_query', ''),
            query_list=obj.get('query_list', []),
            query_summary=obj.get('query_summary', '')
        )

    def to_json(self) -> str:
        """将对象转换为 JSON 字符串"""
        return json.dumps(self.model_dump())

    @classmethod
    def from_json(cls, json_str: str) -> 'StepModelCollection':
        """从 JSON 字符串创建对象"""
        return cls.model_validate(json_str)

    def to_dict(self) -> Dict[str, Any]:
        """将对象转换为字典"""
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StepModelCollection':
        """从字典创建对象"""
        return cls.model_validate(data)