import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# 获取当前脚本文件的目录
base_dir = os.path.dirname(os.path.abspath(__file__))

# 组合成绝对路径，并使用 os.path.abspath 确保路径正确
docs_static_dir = os.path.abspath(os.path.join(base_dir, "../static/docs"))

# 打印实际使用的路径
print(f"Docs static directory: {docs_static_dir}")

# 检查路径是否存在
if not os.path.exists(docs_static_dir):
    print(f"Directory does not exist: {docs_static_dir}")

# 挂载静态文件目录
if os.path.exists(docs_static_dir):
    app.mount("/", StaticFiles(directory=docs_static_dir), name="docs")
else:
    raise RuntimeError("Static directory does not exist")

# 处理 Next.js 路由
@app.get("/{path:path}")
async def catch_all(request: Request, path: str):
    # 处理 HTML 页面
    if path.endswith(".html"):
        file_path = os.path.join(docs_static_dir, path)
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                content = f.read()
            return HTMLResponse(content=content)

    # 处理其他静态文件
    file_path = os.path.join(docs_static_dir, path)
    if os.path.exists(file_path):
        return FileResponse(file_path)

    # 如果文件不存在，返回 404
    return HTMLResponse(content="Not Found", status_code=404)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
