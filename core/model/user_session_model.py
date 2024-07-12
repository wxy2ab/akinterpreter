# models.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict

class UserSession(BaseModel):
    session_id: str
    created_at: datetime
    expires_at: datetime
    last_request_time: datetime
    chat_history: Optional[List[dict]] = Field(default_factory=list)
    current_plan: Optional[Dict] = Field(default_factory=dict)
    step_codes: Optional[Dict] = Field(default_factory=dict)
    data: Optional[Dict] = Field(default_factory=dict)
