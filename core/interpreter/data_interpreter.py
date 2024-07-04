import os
from typing import Any, Tuple
from .code_runner import CodeRunner
from ._interpreter import Interpreter
from ..llms._llm_api_client import LLMApiClient
from ..llms.llm_factory import LLMFactory
from .data_summarizer import DataSummarizer

class DataInterpreter(Interpreter):
    def __init__(self, max_retries=3, is_debug=False):
        self.is_debug = is_debug
        factory = LLMFactory()
        self.llm_client:LLMApiClient = factory.get_instance()
        self.code_runner = CodeRunner()
        self.max_retries = max_retries
        self.pre_installed_libraries = ["pandas", "numpy", "matplotlib", "seaborn", "scipy", "sklearn", "mplfinance"]
        self.output_dir = "output"
        self.figure_dir = os.path.join(self.output_dir, "figures")
        self.data_dir = os.path.join(self.output_dir, "data")
        os.makedirs(self.figure_dir, exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)

    def interpret(self, data: Any, user_request: str) -> Tuple[str, str]:
        self.data = data
        self.data_summary = DataSummarizer.get_data_summary(data)
        self.user_request = user_request
        self.llm_client.clear_chat()

        code = self.generate_code(data, user_request)
        
        for attempt in range(self.max_retries):
            output, error = self.execute_code(code)
            
            if not error:
                break
            
            if attempt < self.max_retries - 1:
                print(f"尝试 {attempt + 1} 失败。正在尝试修复代码...")
                code = self.fix_code(code, error)
            else:
                print(f"所有 {self.max_retries} 次尝试都失败了。无法修复代码。")
        
        report = self.generate_report(output, error, user_request)
        
        return code, report

    def generate_code(self, data: Any, user_request: str) -> str:
        if "data_summary" not in self:
            self.data_summary = DataSummarizer.get_data_summary(data)
        
        prompt = ChinesePrompts.generate_data_code_prompt(
            self.data_summary, 
            user_request, 
            self.pre_installed_libraries, 
            self.figure_dir, 
            self.data_dir
        )
        response = self.llm_client.text_chat(prompt)
        return self.extract_code(response)

    def generate_report(self, data: Any, error: Any, user_request: str) -> str:
        figure_outputs = []
        data_outputs = []
        for line in data.split('\n'):
            if line.startswith('FIGURE_OUTPUT:'):
                figure_outputs.append(line.split(': ')[1])
            elif line.startswith('DATA_OUTPUT:'):
                data_outputs.append(line.split(': ')[1])

        prompt = ChinesePrompts.generate_data_report_prompt(data, error, user_request, figure_outputs, data_outputs)
        markdown_report = self.llm_client.text_chat(prompt)

        corrected_report = markdown_report
        for fig_output in figure_outputs:
            filename, description = fig_output.split(', ')
            corrected_report = corrected_report.replace(f"path/to/{filename}", f"{self.figure_dir}/{filename}")
        
        for data_output in data_outputs:
            filename, description = data_output.split(', ')
            corrected_report = corrected_report.replace(f"path/to/{filename}", f"{self.data_dir}/{filename}")

        return corrected_report

    def fix_code(self, code: str, error: str) -> str:
        prompt = ChinesePrompts.fix_data_code_prompt(code, error, self.data_summary, self.user_request)
        response = self.llm_client.text_chat(prompt)
        return self.extract_code(response)

    def execute_code(self, code: str) -> Tuple[str, str]:
        return self.code_runner.run(code, self.data)

    @staticmethod
    def extract_code(response: str) -> str:
        import re
        code_blocks = re.findall(r'```(?:python)?(.*?)```', response, re.DOTALL)
        
        if code_blocks:
            code = code_blocks[0].strip()
            if 'import' in code and 'data' in code:
                return code
            else:
                raise ValueError("Code block does not contain 'import' or 'data' keyword.")
        else:
            return response.strip()
        

class ChinesePrompts:
    @staticmethod
    def generate_data_code_prompt(data_summary, user_request, pre_installed_libraries, figure_dir, data_dir):
        return f"""根据以下数据摘要和用户请求，生成Python代码来分析数据并满足请求。

数据摘要：
{data_summary}

用户请求：{user_request}

请生成能够完成用户请求的Python代码，基于提供的数据摘要。
遵循以下指导原则：

1. 您可以使用以下预安装的库，无需额外注释：{', '.join(pre_installed_libraries)}。

2. 对于预安装列表之外的任何额外库，请在import语句后包含带有安装说明的注释。例如：
   import requests  # pip install requests

3. 数据处理和分析：
   - 使用 'data' 变量访问输入的数据集。
   - 根据需要进行数据清洗、转换和分析,但不要尝试创建新的'data'变量。
   - 使用适当的统计方法和机器学习算法（如果需要）。

4. 数据可视化：
   - 使用以下函数为每个图形生成唯一的文件名：
     def generate_unique_filename(base_name, extension):
         import uuid
         uuid_str = uuid.uuid4()
         return f"{{base_name}}_{{uuid_str}}.{{extension}}"
   - 将图形保存到以下目录：{figure_dir}
   - 保存每个图形后，按以下格式打印一行：
     FIGURE_OUTPUT: <实际文件名>, <描述性名称>
   示例：
     filename = generate_unique_filename("scatter_plot", "png")
     plt.savefig(os.path.join("{figure_dir}", filename))
     print(f"FIGURE_OUTPUT: {{filename}}, 特征A与特征B的散点图")

5. 输出处理后的数据：
   - 如果生成了新的数据集或处理后的数据，使用generate_unique_filename函数生成文件名
   - 将数据文件保存到以下目录：{data_dir}
   - 保存每个数据文件后，按以下格式打印一行：
     DATA_OUTPUT: <实际文件名>, <描述性名称>
   示例：
     filename = generate_unique_filename("processed_data", "csv")
     processed_data.to_csv(os.path.join("{data_dir}", filename), index=False)
     print(f"DATA_OUTPUT: {{filename}}, 处理后的数据集CSV")

6. 确保代码高效并处理潜在的错误。
7. 包含注释以解释关键的数据处理和分析步骤。

以下是开始的模板：

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn import preprocessing, model_selection, metrics
import os
# 在此处添加任何额外的导入，需要时带有安装注释

def generate_unique_filename(base_name, extension):
    import uuid
    uuid_str = uuid.uuid4()
    return f"{{base_name}}_{{uuid_str}}.{{extension}}"

# 访问输入的数据集
data = data  # 假设数据已经在'data'变量中

# 您的数据处理和分析代码在这里
# ...

请基于此模板和用户的请求提供完整的数据分析代码。"""

    @staticmethod
    def fix_data_code_prompt(code, error, data_summary, user_request):
        return f"""之前的数据分析代码产生了一个错误。请修复它。

代码：
{code}

错误：
{error}

请记住原始的数据摘要和用户请求：

数据摘要：
{data_summary}

用户请求：{user_request}

请提供修正后的代码版本，该版本应解决错误并仍然满足原始的数据分析请求。
确保遵循原始提示中指定的库导入、数据处理、分析、可视化和数据输出的指导原则。
特别注意数据的正确加载和处理，以及generate_unique_filename函数的使用。"""

    @staticmethod
    def generate_data_report_prompt(output, error, user_request, figure_outputs, data_outputs):
        return f"""根据以下数据分析的输出和错误（如果有），提供一个全面的报告来解释结果，包括数据处理步骤、分析发现和创建的可视化。

输出：
{output}

错误：
{error}

原始用户请求：{user_request}

请提供一个清晰简洁的报告，解决用户的原始数据分析请求并解释结果。报告应包括：
1. 数据处理和清洗步骤的概述
2. 主要的分析发现和洞察
3. 对生成的可视化的解释
4. 任何统计结果或模型性能指标（如适用）
5. 对生成的新数据集或处理后数据的描述（如有）

请使用Markdown格式来编写您的响应。

对于创建的任何图形，请使用以下格式引用它们：
![描述](path/to/figure.png)

对于创建的任何数据文件，请使用以下格式引用它们：
[描述](path/to/data_file)

以下是创建的图形和数据文件：
图形：{figure_outputs}
数据文件：{data_outputs}

请确保在您的解释中适当地引用这些图形和数据文件，并详细说明它们如何支持您的分析结果和结论。"""