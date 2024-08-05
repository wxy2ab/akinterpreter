





import json
from typing import Any, Dict, Generator

from tenacity import retry, retry_if_exception, stop_after_attempt

from ..planner.message import send_message
from ..planner.code_enhancement_system import CodeEnhancementSystem
from .llm_tools import LLMTools
from .llm_provider import LLMProvider
from .data_export_step_model import DataExportStepModel
from .step_data import StepData
from ._step_abstract import StepCodeGenerator


class DataExportStepCodeGenerator(StepCodeGenerator):
    def __init__(self,step_info: DataExportStepModel,step_data:StepData):
        self.step_info = step_info
        self.step_data = step_data
        self._step_code = ""
        self.llm_provider = LLMProvider()
        self.llm_tools = LLMTools()
        self.code_enhancement_system = CodeEnhancementSystem()
        self.llm_client = self.llm_provider.new_llm_client()
        self.llms_cheap = self.llm_provider.new_cheap_client()
        self.allow_yfinance = False
    
    @retry(stop=stop_after_attempt(3),retry=retry_if_exception(False))
    def gen_step_code(self) -> Generator[Dict[str, Any], None, None]:
        filetype = self.step_info.filetype
        required_data_list = self.step_info.required_data
        data_summaries = []
        if required_data_list:
            for data_var in required_data_list:
                data_summary =  self.step_data[f"{data_var}_summary"] if f"{data_var}_summary" in self.step_data else "数据摘要不可用"
                data_summaries.append({ "变量" :data_var,"摘要":data_summary})
        
        code_prompt = f"""
        请生成Python代码以将数据导出为{filetype}格式的文件。
        需要导出的数据变量: {', '.join(required_data_list)}
        数据摘要:
        {json.dumps(data_summaries, ensure_ascii=False, indent=2)}
        
        要求：
        1. 使用适当的Python库来处理{filetype}格式。
        2. 确保代码能够处理可能的异常情况。
        3. 如果数据为空，请适当处理。
        4. 生成的文件名应该包含时间戳，以避免覆盖现有文件。
        5. 请提供注释以解释代码的主要部分。
        6. 输出文件必须存储在 ./output/ 目录下，因为只有这个文件夹有写入权限。
           确保在代码中使用 os.path.join('./output', filename) 来构建文件路径。
        
        请仅提供Python代码，无需其他解释。
        """
        
        for chunk in self.llm_client.one_chat(code_prompt, is_stream=True):
            yield send_message(chunk, "code")
            self._step_code += chunk
        
        self._step_code = self.llm_tools.extract_code(self._step_code)
