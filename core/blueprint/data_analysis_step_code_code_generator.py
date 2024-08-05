import json
from typing import Generator, Dict, Any

from ..planner.code_enhancement_system import CodeEnhancementSystem

from .llm_tools import LLMTools

from ..planner.message import send_message

from .llm_provider import LLMProvider
from .step_data import StepData
from .data_analysis_step_model import DataAnalysisStepModel
# 修复：导入BaseStepModel类
from._step_abstract import StepCodeGenerator, BaseStepModel

class DataAnalysisStepCodeGenerator(StepCodeGenerator):
    def __init__(self,step_info: DataAnalysisStepModel,step_data:StepData):
        self.step_info = step_info
        self.step_data = step_data
        self._step_code = ""
        self.llm_provider = LLMProvider()
        self.llm_tools = LLMTools()
        self.code_enhancement_system = CodeEnhancementSystem()
        self.llm_client = self.llm_provider.new_llm_client()
        self.llms_cheap = self.llm_provider.new_cheap_client()
        self.allow_yfinance = False

    def gen_step_code(self) -> Generator[Dict[str, Any], None, None]:
        required_data_list = self.step_info.required_data
        data_summaries = []
        if required_data_list:
            for data_var in required_data_list:
                data_summary =  self.step_data[f"{data_var}_summary"] if f"{data_var}_summary" in self.step_data else "数据摘要不可用"
                data_summaries.append({ "变量" :data_var,"摘要":data_summary})

        code_prompt = self.generate_data_analysis_code_prompt(self.step_info , data_summaries, self.allow_yfinance)
        for chunk in self.llm_client.one_chat(code_prompt, is_stream=True):
            yield send_message(chunk, "code")
            self._step_code += chunk

        self._step_code = self.llm_tools.extract_code(self._step_code)
        yield send_message(self._step_code, "full_code")

    
    def fix_code(self, error: str) -> Generator[str, None, None]:
        if not self._step_code:
            yield send_message("没有可修复的代码。", "error")
            raise Exception("代码还没有生成，还无法修复.")

        fix_prompt = self.fix_code_prompt(self._step_code, error)
        
        fixed_code = ""
        for chunk in self.llm_client.one_chat(fix_prompt, is_stream=True):
            yield send_message(chunk, "code")
            fixed_code += chunk
        
        self._step_code = self.llm_tools.extract_code(fixed_code)
        yield send_message(f"代码已修复。")
        yield send_message(self._step_code, "code")

    def pre_enhancement(self) -> Generator[str, None, None]:
        enhanced_prompt = self.code_enhancement_system.apply_pre_enhancement(
            self.step_info.type,
            self.step_info.description,
            self.step_info.description,
        )
        self.step_info.description = enhanced_prompt
        yield send_message("代码生成提示已增强", "info")
        yield send_message(enhanced_prompt, "enhanced_prompt")

    def post_enhancement(self) -> Generator[str, None, None]:
        retries = 0
        MAX_RETRIES = 5
        enhanced_prompt = self.code_enhancement_system.apply_post_enhancement(self.step_info.type,
                                                                                self.step_info.description,
                                                                                self.step_info.description)
        while retries < MAX_RETRIES:
            # 第一步：检查代码是否有致命错误，要求返回 JSON 格式
            check_prompt = f"""
            请检查以下代码是否有影响运行的致命错误。如果有，请以 JSON 格式列出这些错误，格式如下：
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
            - 如果不是非常确定，不要返回错误，返回空列表，是完全没有问题的。
            - code_tools 是确定可以使用的对象。
            """
            
            check_result = ""
            for chunk in self.llm_client.one_chat(check_prompt, is_stream=True):
                yield send_message(chunk, "code_check")
                check_result += chunk
            
            try:
                errors = self.llm_tools.extract_json_from_text(check_result)
                output,result = self.check_step_result(self._step_code)
                if not result:
                    errors.append({"error":output,"line":"-"})
            except json.JSONDecodeError:
                yield send_message("无法解析检查结果，将假定代码没有错误。", "warning")
                errors = []

            # 如果没有错误，退出循环
            if not errors:
                yield send_message(f"代码检查完成，未发现致命错误。（重试次数：{retries}）", "info")
                break

            # 第二步：如果有致命错误，进行修复
            yield send_message(f"检测到代码中存在 {len(errors)} 个潜在问题，正在进行修复...（重试次数：{retries + 1}）", "info")
            
            error_descriptions = "\n".join([f"- {error['error']} (可能在第 {error['line']} 行)" for error in errors])
            fix_prompt = f"""
            以下代码存在一些问题：
            ```python
            {self._step_code}
            ```

            这些问题包括：
            {error_descriptions}

            请修复这些问题，并提供完整的修正后的代码。修复后的代码使用 ```python 和 ``` 包裹。
            """
            
            fixed_code = ""
            for chunk in self.llm_client.text_chat(fix_prompt, is_stream=True):
                yield send_message(chunk, "code_fix")
                fixed_code += chunk
            
            self._step_code = self.llm_tools.extract_code(fixed_code)
            yield send_message("代码已修复完成。", "info")
            yield send_message(self._step_code, "full_code")

            retries += 1

        if retries == MAX_RETRIES:
            yield send_message(f"达到最大重试次数 ({MAX_RETRIES})，无法完全修复代码。", "warning")
        else:
            yield send_message("代码修复完成，未发现更多错误。", "info")

    @property
    def step_code(self) -> str:
        return self._step_code

    def make_step_sure(self):
        step_number = self.step_info.step_number
        self.step_data.set_step_code(step_number, self._step_code)

    @staticmethod
    def generate_data_analysis_code_prompt(step: DataAnalysisStepModel, data_summaries: list, allow_yfinance: bool) -> str:
        required_data = step.required_data
        save_data_to = step.save_data_to
        step_number = step.step_number

        data_summary_str = "\n".join([f"{summary['变量']}: {summary['摘要']}" for summary in data_summaries])

        return f"""
        生成Python代码来分析以下数据：

        分析任务：{step.description}

        可用的数据变量及其摘要：
        {data_summary_str}

        请遵循以下规则生成代码：

        1. 只生成一个Python代码块，使用 ```python 和 ``` 包裹。
        2. 不要在代码块外添加任何解释或注释。
        3. 使用pandas、matplotlib、seaborn等库进行数据分析和可视化。{'也可以使用yfinance库' if allow_yfinance else '禁止使用yfinance库'}
        4. 所有生成的图片必须保存在 'output' 文件夹下。
        5. 使用 uuid.uuid4() 生成唯一的文件名，以避免重复。
        6. 将生成的文件和图片以Markdown链接的格式写入返回值。
        7. 将主要的分析结果也写入返回值。
        8. 对于新闻分析、情感分析、报告分析等自然语言处理任务，必须使用LLM API进行分析。

        代码结构示例：

        ```python
        import pandas as pd
        import matplotlib.pyplot as plt
        import seaborn as sns
        import uuid
        import os
        from core.utils.code_tools import code_tools

        # 确保output文件夹存在
        os.makedirs('output', exist_ok=True)

        # 访问之前步骤的数据
        {chr(10).join([f"{var} = code_tools['{var}']" for var in required_data])}
        
        # 你的数据分析代码
        # ...

        # 如果需要进行自然语言处理，使用LLM API
        if '需要进行文本分析':
            llm_client = code_tools["llm_client"]
            response = llm_client.one_chat("分析以下文本的情感: " + text_to_analyze)
            # 处理LLM API的响应
            # ...

        # 如果需要获取数据摘要
        data_summarizer = code_tools["data_summarizer"]
        # data_summary = data_summarizer.get_data_summary(your_data)

        # 生成和保存图表
        plt.figure(figsize=(10, 6))
        # 你的绘图代码
        # ...
        file_name = f"output/{{uuid.uuid4()}}.png"
        plt.savefig(file_name)
        plt.close()

        # 准备返回值
        results = []
        results.append(f"![分析图表]({{file_name}})")
        results.append("主要发现：")
        results.append("1. 发现1")
        results.append("2. 发现2")
        # ...

        # 将分析性的结果保存到analysis_result_{step_number}变量,LLM返回的结果也需要保存到这个字符串中
        analysis_result_{step_number} = "\\n".join(results)
        code_tools.add("analysis_result_{step_number}", analysis_result_{step_number})

        # 如果需要保存原始数据
        {"# 请在这里添加保存原始数据的代码" if save_data_to else ""}
        ```

        请确保代码完整可执行，并将分析结果保存在名为'analysis_result_{step_number}'的变量中，这个变量必须是字符串类型。
        {f"同时，请将原始数据保存在名为 {', '.join(save_data_to) if isinstance(save_data_to, list) else save_data_to} 的变量中。" if save_data_to else ""}
        使用 code_tools.add(name, value) 来保存变量。
        如果需要运行代码，可以使用 code_runner = code_tools["code_runner"]，然后使用result_dict = code_runner.run(code, global_vars) 来运行代码。
        """

    @staticmethod
    def fix_code_prompt(code: str, error: str) -> str:
        return f"""
        以下代码导致了一个错误：
        ```python
        {code}
        ```

        错误信息：
        {error}

        请修复代码以解决此错误。提供完整的修正后的代码。
        修复后的代码使用 ```python 和 ``` 包裹。
        """