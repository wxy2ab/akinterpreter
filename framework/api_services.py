import os
import importlib
from fastapi import FastAPI, APIRouter
from fastapi.staticfiles import StaticFiles

class APIService:
    def __init__(self,port=8181):
        self.port = port
        self.app = FastAPI()
        
        self.modules = []
        self.read_args()
        self.load_modules()
        from core.utils.srv_init import service_init_funs
        for func in service_init_funs:
            func()
        
        self.load_routes()
        self.load_directory()

        from core.utils.config_setting import Config
        config = Config()
        if config.has_key("port"):
            self.port = int(config.get("port"))
               
    def load_routes(self):
        import sys
        routes_dir =   os.path.join(sys.path[0], "routes")
        route_files = [f for f in os.listdir(routes_dir) if f.startswith("route_") and f.endswith(".py")]
        
        for route_file in route_files:
            route_module_name = os.path.splitext(route_file)[0]
            route_module = importlib.import_module(f"routes.{route_module_name}")
            
            for attr_name in dir(route_module):
                if attr_name.startswith("router"):
                    router = getattr(route_module, attr_name)
                    if isinstance(router, APIRouter):
                        self.app.include_router(router)
    
    def load_modules(self):
        import sys
        modules_dir = os.path.join(sys.path[0], "modules")

        module_files = [f for f in os.listdir(modules_dir) if f.startswith("module_") and f.endswith(".py")]
        
        for route_file in module_files:
            module_name = os.path.splitext(route_file)[0]
            module = importlib.import_module(f"modules.{module_name}")
            self.modules.append(module)
    
    def load_directory(self):
        html_directory = os.path.abspath("static")
        if not os.path.exists(html_directory):
            os.makedirs(html_directory) 
        self.app.mount("/", StaticFiles(directory=html_directory,html=True), name="static")

    def read_args(self):
        from core.utils.config_setting import Config
        import sys
        config = Config()
        if len(sys.argv) > 1:
            for i in range(1, len(sys.argv), 2):
                if sys.argv[i].startswith("--"):
                    key = sys.argv[i][2:]
                    value = sys.argv[i+1] if i+1 < len(sys.argv) else None
                    config.set(key, value)

    def run(self, host="0.0.0.0"):
        import uvicorn
        uvicorn.run(self.app, host=host, port=self.port)

# 运行服务
if __name__ == "__main__":
    # 创建APIService实例
    service = APIService()
    service.run()