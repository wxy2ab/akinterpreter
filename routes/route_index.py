import os
from fastapi import APIRouter , Response
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse,FileResponse
from fastapi.templating import Jinja2Templates
router = APIRouter()

base_url:str=""
next_base_url:str="static/.next/"

@router.get("/" if base_url == "" else base_url)
def index():
    try:
        return FileResponse("static/.next/server/pages/index.html")
    except FileNotFoundError:
        return {"error": "File not found"}
    except Exception as e:
        return {"error": str(e)}
    
templates = Jinja2Templates(directory="static")

# Helper function to find the correct HTML file
def find_file_path(full_path: str) -> str:
    file_path = f"static/.next/server/pages/{full_path}.html"
    if os.path.exists(file_path):
        return file_path
    
    # Check for dynamic routes
    segments = full_path.split('/')
    for i in range(len(segments)):
        dynamic_path = '/'.join(segments[:i] + ['[id]'] + segments[i+1:])
        file_path = f"static/.next/server/pages/{dynamic_path}.html"
        if os.path.exists(file_path):
            return file_path
    
    # Default to index.html
    return ".next/server/pages/index.html"

@router.get("/{full_path:path}")
async def serve_next(request: Request, full_path: str):
    file_path = find_file_path(full_path)
    return FileResponse(file_path)