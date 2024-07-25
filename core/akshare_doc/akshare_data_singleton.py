import json
from typing import Dict, List, Union
import os

class AKShareDataSingleton:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AKShareDataSingleton, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.classified_functions = self._load_json("json/classified_akshare_functions.json")
        self.akshare_docs = self._load_json("json/akshare_docs.json")
        self.category_summaries = self._load_json("json/classified_summary_akshare.json")
        self.tools_dict_path = self._load_json("json/akshare_tools_dict.json")
        self.completed_querys_json_path = "json/completed_querys.json"
        self.completed_querys = self._load_json(self.completed_querys_json_path)
        from ..patch.makepatch import takepatch
        takepatch()

    def _load_json(self, file_path: str) ->Union[ Dict , List[Dict]]:
        if not os.path.exists(file_path):
            return {}
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _save_json(self, file_path: str, data: Dict):
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def get_completed_querys(self) -> List[Dict]:
        return self.completed_querys

    def save_completed_querys(self):
        self._save_json(self.completed_querys_json_path, self.completed_querys)

    def get_classified_functions(self) -> Dict:
        return self.classified_functions

    def get_akshare_docs(self) -> Dict:
        return self.akshare_docs

    def get_category_summaries(self) -> Dict:
        return self.category_summaries

    def get_tools_dict_path(self) -> Dict:
        return self.tools_dict_path