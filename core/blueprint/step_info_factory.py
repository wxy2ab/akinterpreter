import os
import re
import importlib
from typing import Dict, Type
from ..utils.single_ton import Singleton
from ._step_abstract import StepInfoGenerator

class StepInfoGeneratorFactory(metaclass=Singleton):
    def __init__(self):
        self.step_info_generator_classes: Dict[str, str] = {}  # 存储类名和文件名的映射
        self._discover_step_info_generator_classes()

    def _discover_step_info_generator_classes(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        step_info_generator_pattern = re.compile(r'class\s+(\w+)\s*\([^)]*?(\w+StepInfoGenerator)\):')
        
        for filename in os.listdir(current_dir):
            if filename.endswith('.py') and not filename.startswith('_'):
                file_path = os.path.join(current_dir, filename)
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    matches = step_info_generator_pattern.findall(content)
                    for class_name, _ in matches:
                        self.step_info_generator_classes[class_name.lower()] = filename[:-3]  # 存储类名和模块名的映射

    def get_instance(self, name: str, **kwargs) -> StepInfoGenerator:
        if not name:
            raise ValueError("name cannot be empty")
            
        module_name = self.step_info_generator_classes.get(name.lower())
        if module_name is None:
            raise ValueError(f"No StepInfoGenerator implementation found for name: {name}")
        
        try:
            module = importlib.import_module(f'.{module_name}', package=__package__)
            step_info_generator_class = getattr(module, name)
            return step_info_generator_class(**kwargs)
        except ImportError as e:
            raise ImportError(f"Error importing module {module_name}: {e}")
        except AttributeError:
            raise ValueError(f"Class {name} not found in module {module_name}")

    def list_available_step_info_generators(self) -> list[str]:
        return list(self.step_info_generator_classes.keys())