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
    chat_history: Optional[List[dict]] = Field(default_factory=list)
    current_plan: Optional[Dict] = Field(default_factory=dict)
    step_codes: Optional[Dict] = Field(default_factory=dict)
    data: Optional[Dict] = Field(default_factory=dict)
    def get(self, key: str, default: Any = None) -> Any:
        keys = key.split(".")
        value = self.__dict__  # 获取属性字典，从 data 开始查找

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
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
            if hasattr(value, k):  # 检查属性是否存在
                value = getattr(value, k)  # 获取属性值
                if value is None:  # 判断是否为 None
                    return False
            else:
                return False

        return True
