import asyncio
import json
import os
from typing import Any, Dict
from fastapi import APIRouter, Body, HTTPException , Response
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse,FileResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, ValidationError
from core.session.chat_manager import ChatManager
from core.session.user_session_manager import UserSessionManager
from core.utils.log import logger
router = APIRouter()
manager = UserSessionManager()
chat_manager = ChatManager()


router.prefix = "/api"
from core.utils.log import logger

class PlanRequest(BaseModel):
    session_id: str
    plan: dict

@router.post("/save_plan")
async def save_plan(request: PlanRequest):
    try:
        # Get the raw body
        session_id = request.session_id
        plan = request.plan
        print(f"Received plan for session {session_id}: {json.dumps(plan, indent=2)}")

        chatbot = chat_manager.get_chatbot(session_id)
        if chatbot:
            result = chatbot.save_plan(plan)
            if result != "保存成功":
                logger.debug(f"Warning: Chatbot save_plan returned: {result}")
        else:
            logger.debug(f"Warning: No chatbot found for session {session_id}")

        # Always update the current plan, regardless of chatbot existence
        manager.update_current_plan(session_id, plan)
        return {"message": "计划已经保存!"}

    except ValidationError as e:
        logger.error(f"Validation Error: {str(e)}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
