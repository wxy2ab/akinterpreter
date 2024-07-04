from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple, Union


class Planner(ABC):
    @abstractmethod
    def plan(self,user_requests:str)->Dict[str,Any]:
        pass
    @abstractmethod
    def generate_code_for_data(self,data_retrieval_query:str)->str:
        pass
    @abstractmethod
    def execute_data_retrieval(self,code:str)->Tuple[Any,str]:
        pass
    @abstractmethod
    def generate_code_for_report(self,data:any,data_analysis_query)->str:
        pass
    @abstractmethod
    def execute_data_analysis(self,data:any,code:str)->Tuple[str,str]:
        pass
    @abstractmethod
    def generate_report(self,data:str,query:str)->str:
        pass