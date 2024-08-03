


import json
from typing import Dict, List

from ..blueprint._function_docs_provider import FunctionDocsProvider


class TushareRetrievalProvider(FunctionDocsProvider):
    def __init__(self):
        self.docs = json.load(open("./json/tushare_docs.json"))
    
    def get_specific_doc(self, functions:List[str])->Dict[str,str]:
        return {func: self.docs.get(func, "Documentation not available") for func in functions}