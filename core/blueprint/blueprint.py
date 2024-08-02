import os
import pickle
from typing import Generator

from ._base_step_model import BaseStepModel
from .step_data import StepData
from .blueprint_builder import BluePrintBuilder
from .blueprint_coder import BluePrintCoder
from .blueprint_executor import BluePrintExecutor
from .blueprint_reporter import BluePrintReporter
from .step_model_collection import StepModelCollection
from tenacity import retry, stop_after_attempt

class BluePrint:
    def __init__(self):
        self.blueprint_builder = BluePrintBuilder()
        self.blueprint_coder:BluePrintCoder = None
        self.blueprint_executor:BluePrintExecutor =None
        self.blueprint_reporter:BluePrintReporter = None
        self._blueprint:StepModelCollection =None
        self.max_retry = 3
        self.step_data = StepData()
    
    @property
    def blueprint(self)->StepModelCollection:
        return self._blueprint
    
    def build_blueprint(self,query:str)->Generator[dict[str,any],None,None]:
        yield from self.blueprint_builder.build_blueprint(query)
        self._blueprint = self.blueprint_builder.blueprint

    def modify_blueprint(self,query:str,steps:dict[str,any])->Generator[dict[str,any],None,None]:
        yield from self.blueprint_builder.modify_blueprint(query)
        self._blueprint = self.blueprint_builder.blueprint
    
    def generate_and_execute_all(self)->Generator[dict[str,any],None,None]:
        if self._blueprint is None:
            raise Exception("请先生成蓝图")
        if self.blueprint_coder is None:
            self.blueprint_coder = BluePrintCoder(self._blueprint,self.step_data)
        if self.blueprint_executor is None:
            self.blueprint_executor = BluePrintExecutor(self._blueprint,self.step_data) 
        for step in self._blueprint:
            yield from self.blueprint_coder.generate_step(step)
            yield from self.blueprint_executor.excute_step(step)
    
    def generate_step(self,step:BaseStepModel)->Generator[dict[str,any],None,None]:
        if self._blueprint is None:
            raise Exception("请先生成蓝图")
        if self.blueprint_coder is None:
            self.blueprint_coder = BluePrintCoder(self._blueprint,self.step_data)
        if self.blueprint_executor is None:
            self.blueprint_executor = BluePrintExecutor(self._blueprint,self.step_data) 
        yield from self.blueprint_coder.generate_step(step)
        yield from self.blueprint_executor.excute_step(step)

    def final_report(self)->Generator[dict[str,any],None,None]:
        if self.blueprint_reporter is None:
            self.blueprint_reporter = BluePrintReporter(self._blueprint,self.step_data)
        yield from self.blueprint_reporter.report()

    def clear(self):
        self.blueprint_builder.clear()
        self.step_data = StepData()
        self.blueprint = None

    
    def save_to_file(self, filename: str) -> None:
        """
        将当前 BluePrint 实例序列化到文件
        
        :param filename: 要保存到的文件路径
        """
        data = {
            "blueprint": self._blueprint,
            "step_data": self.step_data,
            "max_retry": self.max_retry
        }
        
        with open(filename, 'wb') as f:
            pickle.dump(data, f)

    @classmethod
    def load_from_file(cls, filename: str) -> 'BluePrint':
        """
        从文件中反序列化并创建一个新的 BluePrint 实例
        
        :param filename: 要加载的文件路径
        :return: 加载了状态的 BluePrint 实例
        """
        if not os.path.exists(filename):
            raise FileNotFoundError(f"文件 {filename} 不存在")

        with open(filename, 'rb') as f:
            data = pickle.load(f)

        instance = cls()
        instance._blueprint = data.get("blueprint")
        instance.step_data = data.get("step_data", StepData())
        instance.max_retry = data.get("max_retry", 3)

        # 重新初始化其他组件
        if instance._blueprint is not None:
            instance.blueprint_coder = BluePrintCoder(instance._blueprint, instance.step_data)
            instance.blueprint_executor = BluePrintExecutor(instance._blueprint, instance.step_data)
            instance.blueprint_reporter = BluePrintReporter(instance._blueprint, instance.step_data)

        return instance