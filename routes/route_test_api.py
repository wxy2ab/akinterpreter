import asyncio
import os
from fastapi import APIRouter, HTTPException , Response
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse,FileResponse
from fastapi.templating import Jinja2Templates
from core.sse.sse_message_queue import SSEMessageQueue
from core.utils.log import logger
router = APIRouter()

router.prefix = "/api"

@router.get("/test")
async def send_test_code(request: Request):
    await push_messages()
    return {"message": "test code have been send!"}


# 推送消息到队列的协程
async def push_messages():
    session_id = "a782f044-79b7-4b78-9b2c-26054af27c6d"
    sse_queue = SSEMessageQueue()

    await sse_queue.put(session_id, {"type": "test", "content": "message 1"})
    await asyncio.sleep(1)
    await sse_queue.put(session_id, {"type": "test", "content": "message 2"})
    await asyncio.sleep(1)
    await sse_queue.put(session_id, "[DONE]")