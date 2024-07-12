from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str

class SessionChatRequest(BaseModel):
    session_id: str
    message: str