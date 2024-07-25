import os
from typing import Any, Tuple, Dict
import pandas as pd
from ._interpreter import Interpreter
from ..llms._llm_api_client import LLMApiClient
from ..llms.llm_factory import LLMFactory
from .code_runner import CodeRunner
from .data_summarizer import DataSummarizer

class ExcelInterpreter(Interpreter):
    def __init__(self, max_retries=3):
        factory = LLMFactory()
        self.llm_client: LLMApiClient = factory.get_instance()
        self.code_runner = CodeRunner()
        self.max_retries = max_retries

    def interpret(self, data: Any, user_request: str) -> Tuple[str, str]:
        excel_path = data if isinstance(data, str) else None
        if not excel_path or not os.path.exists(excel_path):
            return "", "错误：无效的Excel文件路径"

        excel_data, data_summary = self._read_and_summarize_excel(excel_path)
        code = self.generate_code(excel_path, data_summary, user_request)
        
        for attempt in range(self.max_retries):
            output, error = self.execute_code(code, excel_data)
            
            if not error:
                break
            
            if attempt < self.max_retries - 1:
                print(f"尝试 {attempt + 1} 失败。正在尝试修复代码...")
                code = self.fix_code(code, error, data_summary, user_request)
            else:
                print(f"所有 {self.max_retries} 次尝试都失败了。无法修复代码。")
        
        report = self.generate_report(output, error, user_request)
        
        return code, report

    def _read_and_summarize_excel(self, excel_path: str) -> Tuple[Dict[str, pd.DataFrame], str]:
        excel_data = {}
        summaries = []
        
        # 读取所有工作表
        with pd.ExcelFile(excel_path) as xls:
            sheet_names = xls.sheet_names
            for sheet_name in sheet_names:
                excel_data[sheet_name] = pd.read_excel(xls, sheet_name)
        
        # 为每个工作表生成摘要
        summaries.append(f"Excel文件路径: {excel_path}")
        summaries.append(f"工作表数量: {len(sheet_names)}")
        summaries.append("工作表摘要:")
        
        for sheet_name, df in excel_data.items():
            sheet_summary = DataSummarizer.get_data_summary(df)
            summaries.append(f"\n工作表名称: {sheet_name}")
            summaries.append(sheet_summary)
        
        return excel_data, "\n".join(summaries)

    def generate_code(self, excel_path: str, data_summary: str, user_request: str) -> str:
        prompt = ChinesePrompts.create_code_generation_prompt(excel_path, data_summary, user_request)
        response = self.llm_client.text_chat(prompt)
        return self._extract_code(response)

    def generate_report(self, output: Any, error: Any, user_request: str) -> str:
        if error:
            return f"执行过程中发生错误: {error}"
        
        prompt = ChinesePrompts.create_report_generation_prompt(output, user_request)
        report = self.llm_client.text_chat(prompt)
        return report

    def fix_code(self, code: str, error: str, data_summary: str, user_request: str) -> str:
        prompt = ChinesePrompts.create_code_fixing_prompt(code, error, data_summary, user_request)
        response = self.llm_client.text_chat(prompt)
        return self._extract_code(response)

    def execute_code(self, code: str, excel_data: Dict[str, pd.DataFrame]) -> Tuple[Any, str]:
        global_vars = {'data': excel_data}
        return self.code_runner.run(code, global_vars)

    def _extract_code(self, response: str) -> str:
        import re
        code_blocks = re.findall(r'```(?:python)?(.*?)```', response, re.DOTALL)
        
        if code_blocks:
            return code_blocks[0].strip()
        else:
            return response.strip()
    

class ChinesePrompts:
    @staticmethod
    def create_code_generation_prompt(excel_path: str, data_summary: str, user_request: str) -> str:
        return f"""
        根据以下信息生成Python代码来分析Excel文件：
        
        文件路径：{excel_path}
        
        数据摘要：
        {data_summary}
        
        用户请求：
        {user_request}
        
        代码应该：
        1. 使用'data'变量，这是一个字典类型的pandas DataFrame集合。
        每个键是工作表名称，对应的值是该工作表的DataFrame。
        2. 根据请求执行必要的分析或操作，确保使用正确的工作表。
        3. 将结果存储在名为'result'的变量中。
        4. 包含适当的错误处理，特别是在访问特定工作表时。
        
        请只提供Python代码，不需要任何额外的解释。
        """

    @staticmethod
    def create_report_generation_prompt(output: Any, user_request: str) -> str:
        return f"""
        根据以下Excel文件分析输出和原始用户请求，生成一份全面的报告：

        分析输出：
        {output}

        原始用户请求：
        {user_request}

        请提供一份详细的报告，包括：
        1. 执行的分析摘要，提及使用了哪些工作表
        2. 关键发现和洞察
        3. 任何相关的统计数据或数据点
        4. 针对用户特定问题或请求的答复
        5. 任何建议或后续步骤（如适用）

        请使用Markdown格式以提高可读性。
        """

    @staticmethod
    def create_code_fixing_prompt(code: str, error: str, data_summary: str, user_request: str) -> str:
        return f"""
        以下基于用户请求生成的Excel文件分析代码产生了错误。请修复这段代码：

        用户请求：{user_request}

        数据摘要：
        {data_summary}

        代码：
        {code}

        错误：
        {error}

        请提供修正后的Python代码，确保解决错误并满足用户的请求。
        请记住使用'data'变量，这是一个字典类型的pandas DataFrame集合。
        每个键是工作表名称，对应的值是该工作表的DataFrame。
        确保根据用户的请求访问正确的工作表。
        只需包含更新后的代码，不需要任何额外的解释。
        """