


import json
from typing import Any, Dict, Generator, List
from tenacity import retry, retry_if_exception, stop_after_attempt

from ..planner.message import send_message
from ..tushare_doc.tushare_retrieval_provider import TushareRetrievalProvider
from ..planner.code_enhancement_system import CodeEnhancementSystem
from .llm_tools import LLMTools
from .llm_provider import LLMProvider
from .tushare_data_retrieval_step_model import TushareDataRetrievalStepModel
from .step_data import StepData
from ._step_abstract import StepCodeGenerator


class TushareDataRetrievalStepCodeGenerator(StepCodeGenerator):
    def __init__(self, step_info: TushareDataRetrievalStepModel,step_data:StepData):
        self.step_info = step_info
        self.step_data = step_data
        self._step_code = ""
        self.llm_provider = LLMProvider()
        self.llm_client = self.llm_provider.new_llm_client()
        self.llms_cheap = self.llm_provider.new_cheap_client()
        self.akshare_docs_retrieval = TushareRetrievalProvider()
        self.llm_tools = LLMTools()
        self.code_enhancement_system = CodeEnhancementSystem()

    @retry(stop=stop_after_attempt(3),retry=retry_if_exception(False))
    def gen_step_code(self) -> Generator[Dict[str, Any], None, None]:
        selected_functions = self.step_info.selected_functions
        function_docs = self.akshare_docs_retrieval.get_specific_doc(selected_functions)
        
        required_data_list = self.step_info.required_data
        data_summaries = []
        if required_data_list:
            for data_var in required_data_list:
                data_summary =  self.step_data[f"{data_var}_summary"] if f"{data_var}_summary" in self.step_data else "数据摘要不可用"
                data_summaries.append({ "变量" :data_var,"摘要":data_summary})

        code_prompt = self.generate_code_for_data_retrieval_prompt(self.step_info, function_docs, data_summaries)

        for chunk in self.llm_client.one_chat(code_prompt, is_stream=True):
            yield send_message(chunk, "code")
            self._step_code += chunk

        self._step_code = self.llm_tools.extract_code(self._step_code)

        output,result = self.check_step_result(self._step_code)
        if not result:
            yield send_message(output, "error")
            raise Exception(output)

        yield send_message(self._step_code, "full_code")

    def make_step_sure(self):
        step_number = self.step_info.step_number
        self.step_data.set_step_code(step_number, self._step_code)

    @property
    def step_code(self) -> str:
        return self._step_code


    @staticmethod
    def generate_code_for_data_retrieval_prompt(
        step: TushareDataRetrievalStepModel, 
        function_docs: Dict[str, str],
        data_summaries: List[Dict[str, str]]
    ) -> str:
        required_data = [f"{data['变量']}" for data in data_summaries if '变量' in data]
        save_data_to = step.save_data_to
        
        prompt = f"""
        基于以下数据检索任务：
        {step.description}

        考虑使用以下Tushare函数来完成任务：

        {json.dumps(function_docs, indent=2, ensure_ascii=False)}
        """

        if data_summaries:
            prompt += f"""
            之前步骤数据变量的数据摘要：
            {json.dumps(data_summaries, indent=2, ensure_ascii=False)}
            """

        if required_data:
            prompt += f"""
            对于之前步骤的数据，你可以使用以下变量名访问：
            {', '.join(required_data)}
            """

        prompt += f"""
        请生成一个完整的Python代码块来执行任务。遵循以下规则：

        1. 只生成一个Python代码块，使用 ```python 和 ``` 包裹。
        2. 确保代码完整可执行，并将结果保存在指定的变量中。不要使用影响代码直接运行的占位符。
        3. 不要在代码块外添加任何解释或注释。
        4. 代码应考虑数据的时效性、范围、格式和结构，以及可能需要的数据预处理步骤。
        5. 如果需要多个函数配合使用，直接在代码中组合它们。
        6. 使用以下方式导入和使用tushare：
        from core.utils.code_tools import code_tools
        ts = code_tools["ts"]
        pro = ts.pro_api()
        7. 除非特殊说明，存储到结果变量的数据应该是函数返回的原始数据，不要进行额外的处理。
        8. 使用以下方式访问之前步骤的数据：
        from core.utils.code_tools import code_tools
        required_data = code_tools['required_data_name']
        9. 在使用之前步骤的数据时，请参考提供的数据摘要来了解数据的结构和内容。
        10. 使用以下方式保存结果：
            from core.utils.code_tools import code_tools
            
            # 对于每个需要保存的变量：
            {', '.join([f"code_tools.add('{var}', 值)" for var in save_data_to])}
        11. 仔细阅读Tushare文档中每个函数返回数据的限制。
        12. 如果单次请求达到返回数据上限，需要实现多次请求并拼接数据的逻辑。
        13. 很多tushare的查询需要使用ts_code，使用以下方式获取ts_code：
            tsgetter = code_tools["tsgetter"]
            ts_code = tsgetter["查询内容"]
            例如：ts_code = tsgetter["贵州茅台"]
            此时，ts_code 的值将是 "600519.SH" 是可以做其他函数的传入参数的。
            注意：查询美股ts_code时，"查询内容"不能用中文，需要使用英文。

        请只提供代码，不要添加任何额外的解释。代码结构示例：

        ```python
        from core.utils.code_tools import code_tools

        ts = code_tools["ts"]
        pro = ts.pro_api()

        {f"# 访问之前步骤的数据（如果需要）" if required_data else ""}
        {', '.join([f"{var} = code_tools['{var}']" for var in required_data])}

        # 如果查询需要使用ts_code,需要先获取ts_code
        tsgetter = code_tools["tsgetter"]
        ts_code = tsgetter["查询内容"]  # 替换"查询内容"为实际需要查询的股票名称或代码

        # 你的代码逻辑
        # ...

        # 如果需要处理数据限制，实现多次请求并拼接数据
        # ...

        # 保存结果
        {', '.join([f"code_tools.add('{var}', 值)" for var in save_data_to])}
        ```
        """

        return prompt