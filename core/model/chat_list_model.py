from pydantic import BaseModel
from datetime import datetime
from typing import List, Dict, Any
from .user_session_model import UserSession

class ChatListModel(BaseModel):
    session_id:str
    chat_list_id: str
    name: str
    created_at: datetime
    expires_at: datetime
    last_request_time: datetime
    chat_history: List[Dict[str, Any]]
    current_plan: Dict[str, Any]
    step_codes: Dict[int, Any]
    data: Dict[str, Any]

    @staticmethod
    def from_user_session(user_session: UserSession):
        return ChatListModel(
            session_id=user_session.session_id,
            chat_list_id=user_session.chat_list_id,
            created_at=user_session.created_at,
            expires_at=user_session.expires_at,
            last_request_time=user_session.last_request_time,
            chat_history=user_session.chat_history,
            current_plan=user_session.current_plan,
            step_codes=user_session.step_codes,
            data=user_session.data,
            name=user_session.current_plan.get("query_summary",f"{user_session.created_at.strftime("%Y-%m-%d %H:%M")}的计划")
        )
    @staticmethod
    def to_user_session(chat_list: "ChatListModel") -> UserSession:
        return UserSession(
            session_id=chat_list.session_id,
            chat_list_id=chat_list.chat_list_id,
            created_at=chat_list.created_at,
            expires_at=chat_list.expires_at,
            last_request_time=chat_list.last_request_time,
            chat_history=chat_list.chat_history,
            current_plan=chat_list.current_plan,
            step_codes=chat_list.step_codes,
            data=chat_list.data
        )