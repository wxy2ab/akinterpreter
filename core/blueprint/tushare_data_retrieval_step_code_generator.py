


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

    def post_enhancement(self) -> Generator[str, None, None]:
        retries = 0
        MAX_RETRIES = 5
        enhanced_prompt = self.code_enhancement_system.apply_post_enhancement(self.step_info.type,
                                                                                self.step_info.description,
                                                                                self.step_info.description)
        while retries < MAX_RETRIES:
            # 第一步：检查代码中的致命错误，要求返回 JSON 格式
            check_prompt = f"""
            请检查以下代码是否存在会影响其执行的致命错误。如果有，请以 JSON 格式列出这些错误，格式如下：
            ```json
            [
                {{"error": "错误描述1", "line": "可能的问题行号1"}},
                {{"error": "错误描述2", "line": "可能的问题行号2"}}
            ]
            ```
            如果没有错误，请返回空列表：
            ```json
            []
            ```

            代码：
            ```python
            {self._step_code}
            ```

            {f"此外，在检查代码时请考虑以下建议：" if enhanced_prompt else ""}
            {enhanced_prompt if enhanced_prompt else ""}

            注意：
            - 如果您不是非常确定，请不要返回错误。如果没有问题，请返回空列表。
            - code_tools 对象是确定可以使用的。
            - 不允许import tushare as ts ，这个代码是无法运行的，发现这个代码立即报错。必须使用ts=code_tools["ts"]来导入tushare。
            - 不要检查tsgetter['查询内容'],查询内容可以是任意字符串
            - 不要检查pro之中是否存在某个方法，pro是一个tushare的api对象，可以直接调用方法。
            """
            
            check_result = ""
            for chunk in self.llm_client.one_chat(check_prompt, is_stream=True):
                yield send_message(chunk, "code_check")
                check_result += chunk
            
            try:
                errors = self.llm_tools.extract_json_from_text(check_result)
                output, result = self.check_step_result(self._step_code)
                if not result:
                    errors.append({"error": output, "line": "-"})
            except json.JSONDecodeError:
                yield send_message("无法解析检查结果，将假定代码没有错误。", "warning")
                errors = []

            # 如果没有错误，退出循环
            if not errors:
                yield send_message(f"代码检查完成，未发现致命错误。（重试次数：{retries}）", "info")
                break

            # 第二步：如果有致命错误，进行修复
            yield send_message(f"检测到代码中存在 {len(errors)} 个潜在问题，正在进行修复...（重试次数：{retries + 1}）", "info")
            
            error_descriptions = "\n".join([f"- {error['error']} （可能在第 {error['line']} 行）" for error in errors])
            fix_prompt = f"""
            以下代码存在一些问题：
            ```python
            {self._step_code}
            ```

            这些问题包括：
            {error_descriptions}

            {f"此外，在修复代码时请考虑以下增强建议：" if enhanced_prompt else ""}
            {enhanced_prompt if enhanced_prompt else ""}

            请修复这些问题，并提供完整的修正后的代码。修复后的代码使用 ```python 和 ``` 包裹。
            """
            
            fixed_code = ""
            for chunk in self.llm_client.text_chat(fix_prompt, is_stream=True):
                yield send_message(chunk, "code_fix")
                fixed_code += chunk
            
            self._step_code = self.llm_tools.extract_code(fixed_code)
            yield send_message("代码已修复。", "info")
            yield send_message(self._step_code, "full_code")

            retries += 1

        if retries == MAX_RETRIES:
            yield send_message(f"达到最大重试次数（{MAX_RETRIES}），无法完全修复代码。", "warning")
        else:
            yield send_message("代码修复完成，未发现更多错误。", "info")
