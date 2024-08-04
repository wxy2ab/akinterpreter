# models.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Any, Optional, List, Dict

class UserSession(BaseModel):
    session_id: str
    chat_list_id: str
    created_at: datetime
    expires_at: datetime
    last_request_time: datetime
    chat_history: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    current_plan: Optional[Dict[str, Any]] = Field(default_factory=dict)
    step_codes: Optional[Dict[str, Any]] = Field(default_factory=dict)
    data: Optional[Dict[str, Any]] = Field(default_factory=dict)
    def get(self, key: str, default: Any = None) -> Any:
        keys = key.split(".")
        value = self  # 从 self 开始，而不是 self.__dict__

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, default)
                if value == default:
                    return default
            elif hasattr(value, k):
                value = getattr(value, k)
            else:
                return default

        return value
    
    def has(self, key: str) -> bool:
        """
        检查 UserSession 模型中是否存在指定的键，并且值不为 None。

        Args:
            key: 要检查的键。可以是点分隔的路径，表示嵌套字典中的键。

        Returns:
            如果键存在且值不为 None 则返回 True，否则返回 False。
        """
        keys = key.split(".")
        value = self

        for k in keys:
            if hasattr(value, k):
                value = getattr(value, k)
                if value is None:
                    return False
            else:
                return False

        return True
    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }