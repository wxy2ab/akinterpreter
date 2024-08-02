# routers/session.py
from datetime import datetime
import json
from typing import Any, Dict, List
from fastapi import APIRouter, Body, HTTPException, Request
from pydantic import BaseModel, ValidationError
from core.session.chat_manager import ChatManager
from core.session.user_session_manager import UserSessionManager
from core.utils.log import logger

router = APIRouter()
session_manager = UserSessionManager()
router.prefix = "/api"

class PlanModel(BaseModel):
    # Define the expected structure of your plan
    # For example:
    title: str
    steps: List[Dict[str, Any]]
    
@router.post("/sessions")
def create_session():
    session_id = session_manager.add_session_by_id()
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
async def update_current_plan(session_id: str, request: Request):
    try:
        # Get the raw body
        body = await request.body()
        body_str = body.decode('utf-8')

        # Try to parse the JSON
        try:
            current_plan = json.loads(body_str)
        except json.JSONDecodeError as e:
            logger.error(f"JSON Decode Error: {str(e)}")
            # 尝试修复截断的 JSON
            if body_str.endswith('"}]'):
                body_str += '}'
                try:
                    current_plan = json.loads(body_str)
                except json.JSONDecodeError:
                    raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")
            else:
                raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")

        logger.debug(f"Parsed plan: {json.dumps(current_plan, indent=2)}")

        chat_manager = ChatManager()
        result = "保存成功"
        chatbot = chat_manager.get_chatbot(session_id)
        if chatbot:
            result = chatbot.save_plan(current_plan)
        if result == "保存成功":
            session_manager.update_current_plan(session_id, current_plan)
        else:
            raise ValueError(result)
        return {"message": "Current plan updated successfully"}
    except ValidationError as e:
        logger.error(f"Validation Error: {str(e)}")
        raise HTTPException(status_code=422, detail=str(e))
    except ValueError as e:
        logger.error(f"Value Error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

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


