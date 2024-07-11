import os
from fastapi import APIRouter, HTTPException , Response
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse,FileResponse
from fastapi.templating import Jinja2Templates
from core.utils.log import logger
router = APIRouter()

base_url:str=""
next_base_url:str="static/.next/"

@router.get("/" if base_url == "" else base_url)
async def serve_index(request: Request):
    index_path = "static/.next/index.html"
    if os.path.exists(index_path):
        return FileResponse(index_path)
    else:
        return HTMLResponse("Index file not found", status_code=404)


@router.get("/{full_path:path}")
async def serve_static(request: Request, full_path: str):
    logger.debug(f"Received request for path: {full_path}")
    
    try:
        # 优先处理 JavaScript 文件
        if full_path.endswith('.js'):
            js_path = f"static/.next/{full_path}"
            if os.path.exists(js_path):
                logger.debug(f"Serving JavaScript file: {js_path}")
                return FileResponse(js_path, media_type="application/javascript")
        
        if 'output/' in full_path:
            file_path = full_path
            if os.path.exists(file_path):
                logger.debug(f"Serving file: {file_path}")
                return FileResponse(file_path)
            else:
                logger.error(f"File not found: {file_path}")
                raise HTTPException(status_code=404, detail="File not found")

        # 处理其他静态文件
        static_path = f"static/.next/{full_path}"
        if os.path.exists(static_path) and not os.path.isdir(static_path):
            logger.debug(f"Serving static file: {static_path}")
            return FileResponse(static_path)
        
        # 如果不是静态文件，返回 index.html（用于客户端路由）
        index_path = "static/.next/index.html"
        if os.path.exists(index_path):
            logger.debug(f"Serving index.html for path: {full_path}")
            return FileResponse(index_path)
        else:
            logger.error(f"Index file not found: {index_path}")
            raise HTTPException(status_code=404, detail="File not found")
    
    except Exception as e:
        logger.error(f"Error serving file {full_path}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
