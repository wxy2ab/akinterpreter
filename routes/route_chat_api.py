import logging
import os
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
import json
from typing import Union, Dict, Any, Generator
from core.talk.talker_factory import TalkerFactory
import asyncio
from core.session.chat_session_manager import ChatSessionManager
from core.model.chat_request import ChatRequest, SessionChatRequest
from core.utils.log import logger
import traceback

router = APIRouter()
factory = TalkerFactory()
chatbot = factory.get_instance("WebBPTalker")
manager = ChatSessionManager()

from core.session.chat_manager import ChatManager

chat_manager = ChatManager()

@router.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        logger.info(f"Received chat request: {request.message}")
        generator = chatbot.chat(request.message)
        session_id = manager.create_session(generator)
        logger.info(f"Created session with ID: {session_id}")
        return JSONResponse({"session_id": session_id})
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/schat")
async def schat_endpoint(request: SessionChatRequest):
    if os.environ.get("DEBUG_LEVEL") == "debug":
        return await schat_endpoint_debug(request)
    else:
        return await schat_endpoint_production(request)

async def schat_endpoint_debug(request: SessionChatRequest):
    session_id = request.session_id
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required")
    
    logger.info(f"Received chat request for session {session_id}: {request.message}")
    
    chatbot = chat_manager.get_chatbot(session_id)
    if not chatbot:
        chatbot = chat_manager.create_chatbot(session_id)
        logger.info(f"Created new chatbot instance for session ID: {session_id}")
    
    generator = chatbot.chat(request.message)
    chat_sid = manager.create_session(generator)
    return JSONResponse({"session_id": chat_sid})

async def schat_endpoint_production(request: SessionChatRequest):
    try:
        return await schat_endpoint_debug(request)
    except Exception as e:
        logger.error(f"Error in schat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/chat-stream")
async def chat_stream(request: Request):
    session_id = request.query_params.get("session_id")
    logger.info(f"Received stream request for session: {session_id}")
    if not session_id or not manager.session_exists(session_id):
        logger.warning(f"Invalid or missing session ID: {session_id}")
        raise HTTPException(status_code=400, detail="Invalid or missing session ID")

    async def generate():
        try:
            logger.info(f"Starting to generate response for session: {session_id}")
            chat_generator = manager.get_generator(session_id)
            for item in chat_generator:
                logger.debug(f"Generated item: {item}")
                if isinstance(item, str):
                    yield f"data: {json.dumps({'type': 'text', 'content': item})}\n\n"
                elif isinstance(item, dict):
                    if ("content" in item and isinstance(item["content"], BaseModel)) or ("data" in item and isinstance(item["data"], BaseModel)):
                        continue
                    try:
                        serialized_item = json.dumps(item)
                        yield f"data: {serialized_item}\n\n"
                    except TypeError:
                        logger.warning(f"Skipping non-serializable item: {item}")
                        continue
                else:
                    try:
                        yield f"data: {json.dumps({'type': 'unknown', 'content': str(item)})}\n\n"
                    except TypeError:
                        logger.warning(f"Skipping non-serializable item: {item}")
                        continue
                await asyncio.sleep(0)  # 让出控制权给事件循环
            logger.info(f"Finished generating response for session: {session_id}")
            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.error(f"Error in generate function: {str(e)}")
            logger.error(traceback.format_exc())
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
        finally:
            logger.info(f"Clearing session: {session_id}")
            manager.clear_session(session_id)

    return StreamingResponse(generate(), media_type="text/event-stream")