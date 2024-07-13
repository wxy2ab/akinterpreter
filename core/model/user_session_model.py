# models.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Any, Optional, List, Dict

class UserSession(BaseModel):
    session_id: str
    created_at: datetime
    expires_at: datetime
    last_request_time: datetime
    chat_history: Optional[List[dict]] = Field(default_factory=list)
    current_plan: Optional[Dict] = Field(default_factory=dict)
    step_codes: Optional[Dict] = Field(default_factory=dict)
    data: Optional[Dict] = Field(default_factory=dict)
    def get(self, key: str, default: Any = None) -> Any:
        """
        从 UserSession 模型中获取值，支持嵌套字典。

        Args:
            key: 要获取的键。可以是点分隔的路径，表示嵌套字典中的键。
            default: 如果键不存在时的默认返回值。默认为 None。

        Returns:
            键对应的值，如果不存在则返回 default。
        """
        keys = key.split(".")  # 处理嵌套键
        value = self

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default  # 键不存在，返回默认值

        return value
