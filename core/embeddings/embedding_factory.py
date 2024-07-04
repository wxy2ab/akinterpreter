import os
import re
import importlib
from typing import Dict, Type
from ..utils.single_ton import Singleton
from ..utils.config_setting import Config
from ._embedding import Embedding

class EmbeddingFactory(metaclass=Singleton):
    def __init__(self):
        self.embedding_classes: Dict[str, str] = {}  # 存储类名和文件名的映射
        self._discover_embedding_classes()

    def _discover_embedding_classes(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        embedding_pattern = re.compile(r'class\s+(\w+)\s*\([^)]*Embedding[^)]*\):')
        
        for filename in os.listdir(current_dir):
            if filename.endswith('.py') and not filename.startswith('_'):
                file_path = os.path.join(current_dir, filename)
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    matches = embedding_pattern.findall(content)
                    for class_name in matches:
                        self.embedding_classes[class_name.lower()] = filename[:-3]  # 存储类名和模块名的映射

    def get_instance(self, name: str = "") -> Embedding:
        config = Config()
        if name == "" and config.has_key("embedding_api"):
            name = config.get("embedding_api")
            
        module_name = self.embedding_classes.get(name.lower())
        if module_name is None:
            raise ValueError(f"No Embedding implementation found for name: {name}")
        
        try:
            module = importlib.import_module(f'.{module_name}', package=__package__)
            embedding_class = getattr(module, name)
            return embedding_class()
        except ImportError as e:
            raise ImportError(f"Error importing module {module_name}: {e}")
        except AttributeError:
            raise ValueError(f"Class {name} not found in module {module_name}")

    def list_available_embeddings(self) -> list[str]:
        return list(self.embedding_classes.keys())