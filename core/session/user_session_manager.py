# session_manager.py
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import uuid
from ..model.user_session_model import UserSession
from ..db.session_db import SessionDb
from ..utils.single_ton import Singleton

class UserSessionManager(metaclass= Singleton):
    def __init__(self):
        self.db = SessionDb()

    def add_new_session(self) -> str:
        session_id = str(uuid.uuid4())
        now = datetime.now()
        session = UserSession(
            session_id=session_id,
            created_at=now,
            expires_at=now + timedelta(hours=1),
            last_request_time=now
        )
        self.db.add_session(session)
        return session_id

    def add_session(self,session_id:str=None) -> str:
        if not session_id:
            return self.add_new_session()
        now = datetime.now()
        session = UserSession(
            session_id=session_id,
            created_at=now,
            expires_at=now + timedelta(hours=1),
            last_request_time=now
        )
        self.db.add_session(session)
        return session_id

    def get_session(self, session_id: str) -> Optional[UserSession]:
        session = self.db.get_session(session_id)
        if session is None:
            self.add_session(session_id)
            session= self.db.get_session(session_id)
        return session

    def save_session(self, session: UserSession):
        if not self.session_exists(session.session_id):
            raise ValueError("Session does not exist")
        self.db.update_session(session)

    def update_last_request_time(self, session_id: str):
        if not self.session_exists(session_id):
            raise ValueError("Session does not exist")
        self.db.update_last_request_time(session_id, datetime.now())

    def update_chat_history(self, session_id: str, chat_history: List[dict]):
        session = self.get_session(session_id)
        if not session:
            raise ValueError("Session does not exist")
        session.chat_history = chat_history
        self.save_session(session)

    def update_current_plan(self, session_id: str, current_plan: Dict):
        session = self.get_session(session_id)
        if not session:
            raise ValueError("Session does not exist")
        session.current_plan = current_plan
        self.save_session(session)

    def update_step_codes(self, session_id: str, step_codes: Dict):
        session = self.get_session(session_id)
        if not session:
            raise ValueError("Session does not exist")
        session.step_codes = step_codes
        self.save_session(session)

    def update_chat_history1(self, session_id: str, chat_history: List[dict]):
        if not self.session_exists(session_id):
            raise ValueError("Session does not exist")
        self.db.update_chat_history(session_id, chat_history)

    def update_current_plan(self, session_id: str, current_plan: Dict):
        if not self.session_exists(session_id):
            raise ValueError("Session does not exist")
        self.db.update_current_plan(session_id, current_plan)

    def update_step_codes(self, session_id: str, step_codes: Dict):
        if not self.session_exists(session_id):
            raise ValueError("Session does not exist")
        self.db.update_step_codes(session_id, step_codes)

    def update_data(self, session_id: str, data: Dict):
        if not self.session_exists(session_id):
            raise ValueError("Session does not exist")
        self.db.update_data(session_id, data)

    def get_setting_data(self, session_id: str) -> Dict[str, Any]:
        if not self.session_exists(session_id):
            raise ValueError("Session does not exist")
        return self.db.get_data(session_id)
    
    def get_chat_history(self, session_id: str) -> List[dict]:
        if not self.session_exists(session_id):
            raise ValueError("Session does not exist")
        return self.db.get_chat_history(session_id)

    def delete_session(self, session_id: str):
        self.db.delete_session(session_id)

    def session_exists(self, session_id: str) -> bool:
        return self.db.session_exists(session_id)

    def cleanup_sessions(self):
        self.db.cleanup_sessions()

    def get_setting_value(self, session_id: str, key: str) -> Any:
        if not self.session_exists(session_id):
            raise ValueError("Session does not exist")
        setting_data = self.db.get_data(session_id)
        return setting_data.get(key)

    def save_setting_value(self, session_id: str, key: str, value: Any) -> None:
        if not self.session_exists(session_id):
            raise ValueError("Session does not exist")
        setting_data = self.db.get_data(session_id)
        setting_data[key] = value
        self.db.update_data(session_id, setting_data)

    def clear_all(self):
        """Clear all sessions from the database."""
        self.db.delete_all_sessions()