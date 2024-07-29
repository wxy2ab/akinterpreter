

import json
import re
from typing import Any, Dict, List, Union


class LLMTools:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LLMTools, cls).__new__(cls)
            cls._initialized = False
            cls._instance.__init__()
            
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
    
    def extract_json_from_text(self,text: str) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
        json_match = re.search(r'(\[[\s\S]*\]|\{[\s\S]*\})', text)
        if json_match:
            json_str = json_match.group()
            return json.loads(json_str)
        raise json.JSONDecodeError("No valid JSON found in the text", text, 0)
    
    def extract_code(self, content: str) -> str:
        code_match = re.search(r'```python(.*?)```', content, re.DOTALL)
        if code_match:
            return code_match.group(1).strip()
        else:
            return content.strip()