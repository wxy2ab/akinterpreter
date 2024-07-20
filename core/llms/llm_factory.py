import os
import re
import importlib
from typing import Any, Dict, Type
from ..utils.single_ton import Singleton
from ..utils.config_setting import Config
from ._llm_api_client import LLMApiClient
from ..utils.log import logger

class LLMFactory(metaclass=Singleton):
    def __init__(self):
        self.llm_classes: Dict[str, str] = {}  # 存储类名和文件名的映射
        self._discover_llm_classes()

    def _discover_llm_classes(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        llm_api_client_pattern = re.compile(r'class\s+(\w+)\s*\([^)]*LLMApiClient[^)]*\):')
        
        for filename in os.listdir(current_dir):
            if filename.endswith('.py') and not filename.startswith('_'):
                file_path = os.path.join(current_dir, filename)
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    matches = llm_api_client_pattern.findall(content)
                    for class_name in matches:
                        self.llm_classes[class_name.lower()] = filename[:-3]  # 存储类名和模块名的映射

    def get_instance(self, name: str = "",**kwargs) -> LLMApiClient:
        config = Config()
        if name == "" and config.has_key("llm_api"):
            name = config.get("llm_api")
            
        module_name = self.llm_classes.get(name.lower())
        if module_name is None:
            raise ValueError(f"No LLM implementation found for name: {name}")
        
        try:
            module = importlib.import_module(f'.{module_name}', package=__package__)
            llm_class = getattr(module, name)
            return llm_class(**kwargs)
        except ImportError as e:
            raise ImportError(f"Error importing module {module_name}: {e}")
        except AttributeError:
            raise ValueError(f"Class {name} not found in module {module_name}")

    def list_available_llms(self) -> list[str]:
        return list(self.llm_classes.keys())
    
    def class_instantiation(self,name:str) -> Any:
        if name == "LLMFactor":
            try:
                from core.planner.llm_factor import LLMFactor
                client = self.get_instance()
                return LLMFactor(client)
            except Exception as e:
                logger.error(f"Error creating LLMFactor: {e}")
                return None
        return None