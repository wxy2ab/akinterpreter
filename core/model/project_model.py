from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

@dataclass
class Chat:
    id: Optional[int] = None
    project_id: int = 0
    message: str = ""
    timestamp: datetime = datetime.now()

@dataclass
class Project:
    id: Optional[int] = None
    session_id: str = ""
    create_date: datetime = datetime.now()
    project_id: str = ""
    owner: str = ""
    chats: List[Chat] = None

    def __post_init__(self):
        if self.chats is None:
            self.chats = []