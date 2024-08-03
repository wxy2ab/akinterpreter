






from abc import ABC
from typing import Dict, List


class FunctionDocsProvider(ABC):

    def get_specific_doc(self, functions:List[str])->Dict[str,str]:
        pass