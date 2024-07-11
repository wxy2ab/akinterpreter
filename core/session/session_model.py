from datetime import datetime
from uuid import uuid4
from pydantic import BaseModel, Field

class SessionModel(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid4()))
    create_time: datetime = Field(default_factory=datetime.now)
    current_generator: object = None