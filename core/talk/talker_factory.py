import os
import re
import importlib
from typing import Dict
from ..utils.single_ton import Singleton
from ..utils.config_setting import Config
from ._talker import Talker

class TalkerFactory(metaclass=Singleton):
    def __init__(self):
        self.talker_classes: Dict[str, str] = {}  # 存储类名和文件名的映射
        self._discover_talker_classes()

    def _discover_talker_classes(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        #print(f"Searching for Talker classes in: {current_dir}")
        talker_pattern = re.compile(r'class\s+(\w+)\s*\([^)]*Talker[^)]*\):')
        
        for filename in os.listdir(current_dir):
            if filename.endswith('.py') and not filename.startswith('_'):
                file_path = os.path.join(current_dir, filename)
                #print(f"Examining file: {file_path}")
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    matches = talker_pattern.findall(content)
                    for class_name in matches:
                        #print(f"Found Talker class: {class_name} in {filename}")
                        self.talker_classes[class_name.lower()] = filename[:-3]

    def get_instance(self, name: str = "") -> Talker:
        config = Config()
        if name == "" and config.has_key("talker"):
            name = config.get("talker")
            
        module_name = self.talker_classes.get(name.lower())
        if module_name is None:
            raise ValueError(f"No Talker implementation found for name: {name}")
        
        try:
            module = importlib.import_module(f'.{module_name}', package=__package__)
            talker_class = getattr(module, name)
            return talker_class()
        except ImportError as e:
            raise ImportError(f"Error importing module {module_name}: {e}")
        except AttributeError:
            raise ValueError(f"Class {name} not found in module {module_name}")

    def list_available_talkers(self) -> list[str]:
        return list(self.talker_classes.keys())