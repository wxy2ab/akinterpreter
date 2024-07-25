from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple, Union


class Interpreter(ABC):
    @abstractmethod
    def interpret(self,data:any,user_request:str)->Tuple[str,str]:
        """
        解释器
        """
        pass

    def generate_code(self,data:any,user_request:str)->str:
        """
        生成代码
        """
        pass
    def generate_report(self,data:any,error:any,user_request:str)->str:
        """
        生成报告
        """
        pass