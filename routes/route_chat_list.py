from datetime import datetime
import json
from typing import Any, Dict, List
from fastapi import APIRouter, Body, HTTPException, Query, Request
from pydantic import BaseModel, ValidationError
from core.session.chat_manager import ChatManager
from core.session.user_session_manager import UserSessionManager
from core.utils.log import logger

router = APIRouter()
session_manager = UserSessionManager()
router.prefix = "/api"


@router.get("/get_chat_list")
def get_chat_list(session_id: str):
    chat_list = session_manager.chat_list_get_list(session_id)
    return [ {"session_id":session_id,"chat_list_id":chat.chat_list_id ,"name":chat.name,"date":chat.created_at} for chat in chat_list ]

@router.get("/new_chat")
def chat_list_add_new(session_id:str):
    user_session = session_manager.chat_list_add_new(session_id)
    chat_list = session_manager.chat_list_get_list(session_id)
    return [ {"session_id":session_id,"chat_list_id":chat.chat_list_id ,"name":chat.name,"date":chat.created_at} for chat in chat_list ]

@router.get("/change_chat")
def chat_list_change(session_id:str,chat_list_id:str):
    user_session = session_manager.chat_list_change_chat(session_id,chat_list_id)
    return user_session

@router.delete("/delete_chat")
def chat_list_delete(session_id: str = Query(...), chat_list_id: str = Query(...)):
    session_manager.chat_list_delete(chat_list_id)
    return {"message": "chat deleted", "status": True}

