import asyncio
from datetime import datetime
from fastapi import FastAPI
from contextlib import asynccontextmanager
from ..utils.single_ton import Singleton
from .session_model import SessionModel
from .session_model_dict import SessionModelDict

class ChatSessionManager(metaclass=Singleton):
    def __init__(self):
        self.sessions: SessionModelDict = {}
        self.session_timeout = 60 * 60  # 1 hour

    def create_session(self, generator) -> str:
        session = SessionModel(current_generator=generator)
        self.sessions[session.session_id] = session
        return session.session_id

    def get_generator(self, session_id: str):
        return self.sessions[session_id].current_generator

    def clear_session(self, session_id: str):
        self.sessions.pop(session_id, None)

    def session_exists(self, session_id: str) -> bool:
        return session_id in self.sessions

    async def cleanup_expired_sessions(self):
        while True:
            await asyncio.sleep(3600)
            now = datetime.now()
            expired_sessions = [
                session_id for session_id, session in self.sessions.items()
                if (now - session.create_time).total_seconds() > self.session_timeout
            ]
            for session_id in expired_sessions:
                del self.sessions[session_id]

    @asynccontextmanager
    async def lifespan(self, app: FastAPI):
        cleanup_task = asyncio.create_task(self.cleanup_expired_sessions())
        yield
        if cleanup_task:
            cleanup_task.cancel()
            try:
                await cleanup_task
            except asyncio.CancelledError:
                pass