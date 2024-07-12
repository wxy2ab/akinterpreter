# database/session_db.py
import json
import duckdb
from datetime import datetime
from typing import Dict, List, Optional
from ..model.user_session_model import UserSession
from ..utils.single_ton import Singleton

class SessionDb(metaclass=Singleton):
    def __init__(self):
        self.conn = duckdb.connect(database='./database/sessions.db', read_only=False)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS user_sessions (
                session_id VARCHAR PRIMARY KEY,
                created_at TIMESTAMP,
                expires_at TIMESTAMP,
                last_request_time TIMESTAMP,
                chat_history JSON,
                current_plan JSON,
                step_codes JSON,
                data JSON
            )
        """)

    def add_session(self, session: UserSession):
        self.conn.execute(
            "INSERT INTO user_sessions (session_id, created_at, expires_at, last_request_time, chat_history, current_plan, step_codes, data) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                session.session_id,
                session.created_at,
                session.expires_at,
                session.last_request_time,
                json.dumps(session.chat_history),
                json.dumps(session.current_plan),
                json.dumps(session.step_codes),
                json.dumps(session.data)
            )
        )

    def get_session(self, session_id: str) -> Optional[UserSession]:
        result = self.conn.execute(
            "SELECT session_id, created_at, expires_at, last_request_time, chat_history, current_plan, step_codes, data FROM user_sessions WHERE session_id = ?",
            (session_id,)
        ).fetchone()

        if result:
            return UserSession(
                session_id=result[0],
                created_at=result[1],
                expires_at=result[2],
                last_request_time=result[3],
                chat_history=json.loads(result[4]),
                current_plan=json.loads(result[5]),
                step_codes=json.loads(result[6]),
                data=json.loads(result[7])
            )
        return None

    def update_session(self, session: UserSession):
        self.conn.execute(
            "UPDATE user_sessions SET created_at = ?, expires_at = ?, last_request_time = ?, chat_history = ?, current_plan = ?, step_codes = ?, data = ? WHERE session_id = ?",
            (session.created_at, session.expires_at, session.last_request_time, session.chat_history, session.current_plan, session.step_codes, session.data, session.session_id)
        )

    def update_last_request_time(self, session_id: str, last_request_time: datetime):
        self.conn.execute(
            "UPDATE user_sessions SET last_request_time = ? WHERE session_id = ?",
            (last_request_time, session_id)
        )

    def update_chat_history(self, session_id: str, chat_history: List[dict]):
        self.conn.execute(
            "UPDATE user_sessions SET chat_history = ? WHERE session_id = ?",
            (json.dumps(chat_history), session_id)
        )

    def update_current_plan(self, session_id: str, current_plan: Dict):
        self.conn.execute(
            "UPDATE user_sessions SET current_plan = ? WHERE session_id = ?",
            (json.dumps(current_plan), session_id)
        )

    def update_step_codes(self, session_id: str, step_codes: Dict):
        self.conn.execute(
            "UPDATE user_sessions SET step_codes = ? WHERE session_id = ?",
            (json.dumps(step_codes), session_id)
        )

    def update_data(self, session_id: str, data: Dict):
        self.conn.execute(
            "UPDATE user_sessions SET data = ? WHERE session_id = ?",
            (json.dumps(data), session_id)
        )

    def delete_session(self, session_id: str):
        self.conn.execute("DELETE FROM user_sessions WHERE session_id = ?", (session_id,))

    def session_exists(self, session_id: str) -> bool:
        result = self.conn.execute("SELECT 1 FROM user_sessions WHERE session_id = ?", (session_id,)).fetchone()
        return result is not None

    def cleanup_sessions(self):
        now = datetime.now()
        self.conn.execute("DELETE FROM user_sessions WHERE expires_at < ?", (now,))
