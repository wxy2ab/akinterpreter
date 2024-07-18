import asyncio
import json
import os
from typing import Any, Dict
from fastapi import APIRouter, Body, HTTPException , Response
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse,FileResponse
from fastapi.templating import Jinja2Templates
from core.session.chat_manager import ChatManager
from core.session.user_session_manager import UserSessionManager
from core.utils.log import logger
router = APIRouter()
manager = UserSessionManager()
chat_manager = ChatManager()


router.prefix = "/api"

@router.post("/save_plan")
async def send_plan(session_id: str, plan:  Dict[str, Any] = Body(...)):
    chatbot=chat_manager.get_chatbot(session_id)
    result = chatbot.save_plan(plan)
    if result=="保存成功":
        manager.update_current_plan(session_id,plan)
        return {"message": "计划已经保存!"}
    else:
        return {"message": result}

