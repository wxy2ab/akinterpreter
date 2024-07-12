# routers/session.py
from datetime import datetime
from typing import Dict, List
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from core.sse.sse_message_queue import SSEMessageQueue
router = APIRouter()
router.prefix = "/api"


sse_queue = SSEMessageQueue()

@router.get("/sse")
async def sse(request: Request, session_id: str = Query(...)):
    async def event_generator():
        while True:
            if await request.is_disconnected():
                break
            message = await sse_queue.get(session_id)
            yield f"data: {message}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.post("/send_message")
async def send_message(session_id: str, message: str):
    await sse_queue.put(session_id, message)
    return {"message": "Message sent to queue"}