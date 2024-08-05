



from typing import Any, Dict, Generator, Type

from ..planner.message import send_message


from .data_export_step_executor import DataExportStepExecutor

from .data_export_step_code_generator import DataExportStepCodeGenerator
from ._base_step_model import BaseStepModel
from .data_export_step_model import DataExportStepModel
from ._step_abstract import StepCodeGenerator, StepExecutor, StepInfoGenerator


class DataExportStepInfoGenerator(StepInfoGenerator):
    def __init__(self) -> None:
        pass

    @property
    def step_description(self) -> str:
        return "提供数据导出到文件的步骤。这个步骤需要填写filetype,可以是csv, json, xml, xlsx, markdown 。默认为 csv"
    
    @property
    def step_model(self) -> Type[BaseStepModel]:
        return DataExportStepModel

    @property
    def step_code_generator(self) -> Type["StepCodeGenerator"]:
        return DataExportStepCodeGenerator
    
    @property
    def step_executor(self) -> Type["StepExecutor"]:
        return DataExportStepExecutor
    
    def get_step_model(self) -> BaseStepModel:
        return DataExportStepModel()

    def gen_step_info(self, step_info :dict, query:str)-> Generator[Dict[str, Any], None, DataExportStepModel]:
        step = DataExportStepModel()
        step.description = step_info["task"]
        step.save_data_to=step_info["save_data_to"]
        step.required_data=step_info["required_data"]
        if "filetype" in step_info:
            step.filetype = step_info["filetype"]
        yield send_message(type="plan",content="\n优化变量控制\n")
        yield send_message(type="plan",content="完成步骤\n")
        return step

    def validate_step_info(self, step_info:dict)-> tuple[str, bool]:
        required_data = step_info.get("required_data")
        save_data_to = step_info.get("save_data_to")
        filetype = step_info.get("filetype")
        allowed_filetypes = ['csv', 'json', 'parquet','xml','xlsx','markdown' ,'html','pdf','docx']
        if len(required_data):
            return "data_export步骤的 required_data 必须有值，否则无法把数据导出",False
        if len(save_data_to)>0:
            return "data_export步骤的 save_data_to 不需要，因为不会生成新的数据",False
        if filetype not in allowed_filetypes:
            return "data_export步骤的 filetype 必须是 csv, json, xml, xlsx, markdown 中的一个",False
        return "",True

    def fix_step_info(self, step_data, query, error_msg) -> Generator[Dict[str, Any], None, None]:
        yield send_message("fix finieshed", "message")