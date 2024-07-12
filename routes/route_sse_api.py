# routers/session.py
import asyncio
from datetime import datetime
import json
from typing import Dict, List
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import JSONResponse, StreamingResponse
from core.sse.sse_message_queue import SSEMessageQueue
router = APIRouter()
router.prefix = "/api"
from core.utils.log import logger

sse_queue = SSEMessageQueue()

@router.get("/sse")
async def sse(request: Request):
    session_id = request.query_params.get("session_id")
    logger.info(f"Received SSE request for session: {session_id}")
    try:
        async def event_generator():
            while True:
                if await request.is_disconnected():
                    break
                try:
                    message = await sse_queue.get(session_id)
                    yield f"data: {json.dumps(message)}\n\n"
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Error in event_generator: {str(e)}")
                    yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")
    except Exception as e:
        logger.error(f"Error in SSE: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": "Internal Server Error"},
        )

@router.post("/send_message")
async def send_message(session_id: str, plan: dict, step_codes: dict):
    message = {"plan": plan, "step_codes": step_codes}
    await sse_queue.put(session_id, message)
    return {"message": "Message sent to queue"}