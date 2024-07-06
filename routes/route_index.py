from fastapi import APIRouter , Response
router = APIRouter()

base_url:str=""

@router.get("/" if base_url == "" else base_url)
def index():
    try:
        with open("static/index.html", "r") as file:
            content = file.read()
        return Response(content=content, media_type="text/html")
    except FileNotFoundError:
        return {"error": "File not found"}
    except Exception as e:
        return {"error": str(e)}