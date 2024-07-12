# routers/session.py
from datetime import datetime
from typing import Dict, List
from fastapi import APIRouter, HTTPException
from core.session.user_session_manager import UserSessionManager

router = APIRouter()
session_manager = UserSessionManager()
router.prefix = "/api"

@router.post("/sessions")
def create_session():
    session_id = session_manager.add_session()
    return {"session_id": session_id}

@router.get("/sessions/{session_id}")
def get_session(session_id: str):
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@router.put("/sessions/{session_id}")
def save_session(session_id: str, data: dict):
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session.data.update(data)
    session_manager.save_session(session)
    return {"message": "Session updated successfully"}

@router.put("/sessions/{session_id}/chat_history")
def update_chat_history(session_id: str, chat_history: List[dict]):
    try:
        session_manager.update_chat_history(session_id, chat_history)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"message": "Chat history updated successfully"}

@router.put("/sessions/{session_id}/current_plan")
def update_current_plan(session_id: str, current_plan: Dict):
    try:
        session_manager.update_current_plan(session_id, current_plan)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"message": "Current plan updated successfully"}

@router.put("/sessions/{session_id}/step_codes")
def update_step_codes(session_id: str, step_codes: Dict):
    try:
        session_manager.update_step_codes(session_id, step_codes)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"message": "Step codes updated successfully"}

@router.put("/sessions/{session_id}/data")
def update_data(session_id: str, data: Dict):
    try:
        session_manager.update_data(session_id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"message": "Data updated successfully"}

@router.get("/sessions/{session_id}/fetch_data")
def fetch_session_data(session_id: str):
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "chat_history": session.chat_history,
        "current_plan": session.current_plan,
        "step_codes": session.step_codes
    }

@router.delete("/sessions/{session_id}")
def delete_session(session_id: str):
    if not session_manager.session_exists(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    session_manager.delete_session(session_id)
    return {"message": "Session deleted successfully"}

@router.post("/sessions/cleanup")
def cleanup_sessions():
    session_manager.cleanup_sessions()
    return {"message": "Expired sessions cleaned up"}
