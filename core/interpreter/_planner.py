from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple, Union


class Planner(ABC):
    @abstractmethod
    def plan(self,user_requests:str)->Dict[str,Any]:
        pass
    @abstractmethod
    def generate_code_for_data(self,data_retrieval_query:str,code:str=None,error:str=None)->str:
        pass
    @abstractmethod
    def execute_data_retrieval(self,code:str,golbal_vars:Dict[str,Any]={})->Tuple[Any,str]:
        pass
    @abstractmethod
    def generate_code_for_report(self,data:any,data_analysis_query,code:str=None,error:str=None)->str:
        pass
    @abstractmethod
    def execute_data_analysis(self,data:any,code:str,golbal_vars:Dict[str,Any]={})->Tuple[str,str]:
        pass
    @abstractmethod
    def generate_report(self,data:str,query:str)->str:
        pass
    @abstractmethod
    def plan_and_execute(self,user_requests:str,data:any)->Tuple[str,str]:
        pass