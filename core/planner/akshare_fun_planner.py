from datetime import datetime
import os
import re
from ..akshare_doc.akshare_data_singleton import AKShareDataSingleton
from typing import List, Dict, Tuple, Union,Optional,Any
import json
from typing import Generator, Dict, Any, List, Optional
from ..llms.llm_factory import LLMFactory
from ..llms._llm_api_client import LLMApiClient
from ..interpreter.sse_code_runner import SSECodeRunner
from ..interpreter.data_summarizer import DataSummarizer
from ..interpreter._sse_planner import SSEPlanner, RetrievalProvider


class AkshareRetrievalProvider:
    def __init__(self):
        self.data_singleton = AKShareDataSingleton()
        self.category_summaries = self.data_singleton.get_category_summaries()
        self.classified_functions = self.data_singleton.get_classified_functions()
        self.akshare_docs = self.data_singleton.get_akshare_docs()


    def get_categories(self) -> Dict[str, str]:
        """
        返回可用的数据类别字典
        :return: 字典，键为类别名称，值为类别描述
        """
        return self.category_summaries

    def get_functions(self, categories: List[str]) -> Dict[str, List[str]]:
        """
        根据给定的类别返回相关函数
        :param categories: 类别列表
        :return: 字典，键为类别，值为该类别下的函数列表
        """
        result = {}
        for category in categories:
            if category in self.classified_functions:
                functions = self.classified_functions[category]
                result[category] = [self._extract_function_name(func) for func in functions]
        return result

    def _extract_function_name(self, function_string: str) -> str:
        """
        从函数字符串中提取函数名
        :param function_string: 包含函数名和描述的字符串
        :return: 函数名
        """
        match = re.match(r"(\w+):", function_string)
        if match:
            return match.group(1)
        else:
            # 如果无法提取函数名，返回整个字符串
            return function_string

    def get_specific_doc(self, functions: List[str]) -> Dict[str, str]:
        """
        获取指定函数的文档
        :param functions: 函数名列表
        :return: 字典，键为函数名，值为对应的文档
        """
        return {func: self.akshare_docs.get(func, "Documentation not available") for func in functions}

class AksharePrompts:
    @staticmethod
    def create_plan_prompt(query: str, categories: Dict[str, str]) -> str:
        return f"""
        基于用户查询："{query}"
        以及可用的数据类别：
        {json.dumps(categories, indent=2, ensure_ascii=False)}

        创建一个详细的计划来检索和分析数据。请注意以下要点：
        1. 不同类型的数据可能需要通过不同的步骤分别获取。
        2. 每个数据检索步骤应该专注于获取一种特定类型的数据。
        3. 在所有必要的数据都获取之后，再进行数据分析步骤。

        该计划应采用JSON格式，具有以下结构：
        {{
            "query_summary": "查询的总结和提炼",
            "steps": [
                {{
                    "step_number": 1,
                    "description": "步骤描述",
                    "type": "data_retrieval",
                    "data_category": "相关数据类别",
                    "save_data_to": "描述性的变量名，如 china_stock_index_data"
                }},
                // 可能有多个数据检索步骤
                {{
                    "step_number": 2,
                    "description": "步骤描述",
                    "type": "data_analysis",
                    "required_data": ["之前步骤中的 save_data_to 变量名列表"]
                }}
            ]
        }}

        请确保：
        1. 包含查询的总结和提炼。
        2. 每个步骤都有一个唯一的 step_number。
        3. 每个 data_retrieval 步骤都有一个描述性的 save_data_to 变量名。
        4. 每个 data_analysis 步骤的 required_data 列表包含了它需要的所有数据的变量名。
        5. 变量名应该是描述性的，易于理解的，如 china_stock_index_data, us_market_sentiment 等。
        6. 计划包括所有必要的数据检索步骤，以及后续的数据分析步骤。

        请提供完整的JSON格式计划，确保其可以被直接解析为Python字典。
        """

    @staticmethod
    def modify_plan_prompt(query: str, current_plan: Dict[str, Any]) -> str:
        return f"""
        基于用户的新要求："{query}"
        以及当前的计划：
        {json.dumps(current_plan, indent=2, ensure_ascii=False)}

        请修改当前计划以适应新的要求。在修改时，请注意：
        1. 保持计划的整体结构不变。
        2. 根据新的要求添加、删除或修改步骤。
        3. 确保步骤编号的连续性和正确性。
        4. 更新 query_summary 以反映新的要求。
        5. 确保数据分析步骤的 required_data 与数据检索步骤的 save_data_to 保持一致。

        请提供修改后的完整JSON格式计划，确保其可以被直接解析为Python字典。
        """
    
    @staticmethod
    def generate_code_for_functions_prompt(step: Dict[str, Any], function_docs: Dict[str, str]) -> str:
        return f"""
        基于以下数据检索任务：
        {step['description']}

        考虑使用以下Akshare函数来完成任务：

        {json.dumps(function_docs, indent=2, ensure_ascii=False)}

        请生成一个完整的Python代码块来执行任务。遵循以下规则：

        1. 只生成一个Python代码块，使用 ```python 和 ``` 包裹。
        2. 确保代码完整可执行，并将结果保存在一个名为'{step['save_data_to']}'的变量中。
        3. 不要在代码块外添加任何解释或注释。
        4. 代码应考虑数据的时效性、范围、格式和结构，以及可能需要的数据预处理步骤。
        5. 如果需要多个函数配合使用，直接在代码中组合它们。
        6. 确保最终结果被赋值给变量 '{step['save_data_to']}'，而不是其他名称。

        请只提供代码，不要添加任何额外的解释。
        """

    @staticmethod
    def select_data_category_prompt(step: Dict[str, Any], categories: Dict[str, str]) -> str:
        return f"""
        基于以下数据检索任务：
        {step['description']}

        从以下数据类别中选择最合适的一个：
        {json.dumps(categories, indent=2, ensure_ascii=False)}

        请只返回选中的类别名称，不需要其他解释。
        """

    @staticmethod
    def select_functions_from_category_prompt(step: Dict[str, Any], functions: List[str]) -> str:
        return f"""
        基于以下数据检索任务：
        {step['description']}

        从以下函数中选择1到5个最合适的函数：
        {json.dumps(functions, indent=2, ensure_ascii=False)}

        请返回选中的函数名称列表，用逗号分隔。不需要其他解释。
        """

    @staticmethod
    def generate_data_analysis_code_prompt(step: Dict[str, Any], data_summaries: Dict[str, str],allow_yfinance:bool) -> str:
        return f"""
        生成一个Python代码块来分析以下数据：

        数据摘要：
        {json.dumps(data_summaries, indent=2, ensure_ascii=False)}

        分析任务：{step['description']}

        请遵循以下规则生成代码：

        1. 只生成一个Python代码块，使用 ```python 和 ``` 包裹。
        2. 不要在代码块外添加任何解释或注释。
        3. 使用pandas、matplotlib、seaborn等库进行数据分析和可视化。{'也可以使用yfinance库' if allow_yfinance else '禁止使用yfinance库'}
        4. 所有生成的图片必须保存在 'output' 文件夹下。
        5. 使用 uuid.uuid4() 生成唯一的文件名，以避免重复。
        6. 将生成的文件和图片以Markdown链接的格式写入返回值。
        7. 将主要的分析结果也写入返回值。
        8. 对于新闻分析、情感分析等自然语言处理任务，必须使用LLM API进行分析。

        如果需要使用LLM API进行分析，请使用以下代码获取一个新的LLMApiClient实例：

        llm_client = llm_factory.get_instance()
        response = llm_client.one_chat("你的提示词")  # 单次分析任务用one_chat(str)方法, 多次分析任务用换成text_chat(str)方法

        可用的变量和对象：
        - llm_factory: LLMFactory 实例，用于获取新的 LLMApiClient
        - code_runner: CodeRunner 实例
        - data_summarizer: DataSummarizer 实例
        - retriever: RetrievalProvider 实例，用于获取额外的数据检索信息

        对于之前步骤的数据，你可以使用以下变量名访问：
        {', '.join(step['required_data'])}

        代码结构示例：

        ```python
        import pandas as pd
        import matplotlib.pyplot as plt
        import seaborn as sns
        import uuid
        import os

        # 确保output文件夹存在
        os.makedirs('output', exist_ok=True)

        # 访问之前步骤的数据
        # 例如：data = {step['required_data'][0]}

        # 你的数据分析代码
        # ...

        # 如果需要进行自然语言处理，使用LLM API
        if '需要进行文本分析':
            llm_client = llm_factory.get_instance()
            response = llm_client.one_chat("分析以下文本的情感: " + text_to_analyze)
            # 处理LLM API的响应
            # ...

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

        # 将结果保存到analysis_result变量
        analysis_result = "\\n".join(results)
        ```

        请确保代码完整可执行，并将分析结果保存在名为'analysis_result'的变量中。
        """

    @staticmethod
    def fix_code_prompt(code: str, error: str) -> str:
        return f"""
        以下代码导致了一个错误：
        {code}

        错误信息：
        {error}

        请修复代码以解决此错误。提供完整的修正后的代码。
        """

    @staticmethod
    def create_report_prompt(initial_query: str, results_summary: str) -> str:
        return f"""
        基于以下初始查询和分析结果，生成一份全面的报告：

        初始查询：
        {initial_query}

        分析结果：
        {results_summary}

        请生成一份全面的报告，总结数据分析的发现和洞察。报告应该：
        1. 回答初始查询
        2. 总结每个分析任务的主要发现
        3. 提供整体的见解和结论
        4. 指出任何有趣或意外的发现
        5. 如果适用，提供进一步分析的建议

        报告应结构清晰、表述明确，并提供有意义的结论。
        """

class PlanManager:
    def __init__(self):
        self.current_plan: Optional[Dict[str, Any]] = None
        self.current_step: int = 0
        self.total_steps: int = 0
        self.is_plan_confirmed: bool = False
        self.execution_results: List[Dict[str, Any]] = []

    def create_plan(self, plan_json: str) -> Dict[str, Any]:
        try:
            plan = json.loads(plan_json)
            self.current_plan = plan
            self.total_steps = len(plan['steps'])
            return plan
        except json.JSONDecodeError:
            raise ValueError("无法创建有效的计划。提供的 JSON 字符串无法解析。")

    def modify_plan(self, plan_json: str) -> Dict[str, Any]:
        if not self.current_plan:
            raise ValueError("没有可修改的计划。请先创建一个计划。")
        
        try:
            plan = json.loads(plan_json)
            self.current_plan = plan
            self.total_steps = len(plan['steps'])
            return plan
        except json.JSONDecodeError:
            raise ValueError("无法修改计划。提供的 JSON 字符串无法解析。")

    def confirm_plan(self) -> None:
        if not self.current_plan:
            raise ValueError("没有可确认的计划。请先创建一个计划。")
        self.current_step = 0
        self.is_plan_confirmed = True
        self.execution_results = []

    def get_current_step(self) -> Optional[Dict[str, Any]]:
        if not self.current_plan or self.current_step >= len(self.current_plan['steps']):
            return None
        return self.current_plan['steps'][self.current_step]

    def add_execution_result(self, result: Dict[str, Any]) -> None:
        self.execution_results.append(result)

    def next_step(self) -> None:
        if self.current_step < self.total_steps - 1:
            self.current_step += 1
        else:
            self.is_plan_confirmed = False  # 计划执行完毕

    def is_plan_complete(self) -> bool:
        return self.current_step >= self.total_steps

    def get_plan_summary(self) -> str:
        if not self.current_plan:
            return "当前没有计划。"
        
        summary = f"查询摘要: {self.current_plan['query_summary']}\n"
        summary += f"总步骤数: {self.total_steps}\n"
        summary += f"当前步骤: {self.current_step + 1}\n"
        summary += "步骤详情:\n"
        for i, step in enumerate(self.current_plan['steps'], 1):
            summary += f"  {i}. {step['description']} ({step['type']})\n"
        return summary

    def save_state(self) -> Dict[str, Any]:
        return {
            "current_plan": self.current_plan,
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "is_plan_confirmed": self.is_plan_confirmed,
            "execution_results": self.execution_results
        }

    def load_state(self, state: Dict[str, Any]) -> None:
        self.current_plan = state.get("current_plan")
        self.current_step = state.get("current_step", 0)
        self.total_steps = state.get("total_steps", 0)
        self.is_plan_confirmed = state.get("is_plan_confirmed", False)
        self.execution_results = state.get("execution_results", [])

    def reset(self) -> None:
        self.__init__()
    
class CodeGenerator:
    def __init__(self, llm_client: Any, retriever: Any, prompts: Any):
        self.llm_client = llm_client
        self.retriever = retriever
        self.prompts = prompts

    def generate_data_retrieval_code(self, step: Dict[str, Any]) -> Generator[Union[Dict[str, Any], str], None, None]:
        category = step['data_category']
        selected_functions = yield from self._select_functions_from_category(step, category)
        function_docs = self.retriever.get_specific_doc(selected_functions)
        code_prompt = self.prompts.generate_code_for_functions_prompt(step, function_docs)
        yield from self._generate_code(code_prompt)

    def generate_data_analysis_code(self, step: Dict[str, Any], data_summaries: Dict[str, str], allow_yfinance: bool) -> Generator[Union[Dict[str, Any], str], None, None]:
        code_prompt = self.prompts.generate_data_analysis_code_prompt(step, data_summaries, allow_yfinance)
        yield from self._generate_code(code_prompt)

    def fix_code(self, code: str, error: str) -> Generator[str, None, None]:
        fix_prompt = self.prompts.fix_code_prompt(code, error)
        yield from self._generate_code(fix_prompt)

    def _select_functions_from_category(self, step: Dict[str, Any], category: str) -> Generator[List[str], None, None]:
        functions = self.retriever.get_functions([category])
        function_prompt = self.prompts.select_functions_from_category_prompt(step, functions[category])
        
        full_response = ""
        for chunk in self.llm_client.text_chat(function_prompt, is_stream=True):
            full_response += chunk
            yield {"type": "function_selection_progress", "content": chunk}

        selected_functions = [func.strip() for func in full_response.split(',')]
        yield {"type": "function_selection", "content": f"已选择函数：{', '.join(selected_functions)}"}
        return selected_functions

    def _generate_code(self, prompt: str) -> Generator[Union[Dict[str, Any], str], None, None]:
        full_code = ""
        for chunk in self.llm_client.text_chat(prompt, is_stream=True):
            full_code += chunk
            yield {"type": "code_generation_progress", "content": chunk}
        
        extracted_code = self._extract_code(full_code)
        yield {"type": "code_generation", "content": full_code}
        yield extracted_code

    def _extract_code(self, content: str) -> str:
        code_blocks = re.findall(r'```(?:python)?(.*?)```', content, re.DOTALL)
        if code_blocks:
            return '\n'.join(block.strip() for block in code_blocks)
        
        lines = content.split('\n')
        code_lines = []
        in_code_block = False
        for line in lines:
            stripped_line = line.strip()
            if stripped_line.startswith('import ') or stripped_line.startswith('from ') or in_code_block:
                code_lines.append(line)
                in_code_block = True
            elif in_code_block and (stripped_line == '' or stripped_line.startswith('#')):
                code_lines.append(line)
            elif in_code_block and not (stripped_line.startswith('import ') or stripped_line.startswith('from ')):
                if any(keyword in stripped_line for keyword in ['def ', 'class ', 'if ', 'for ', 'while ', 'return ', '=']):
                    code_lines.append(line)
                else:
                    in_code_block = False

        if code_lines:
            return '\n'.join(code_lines).strip()

        return content.strip()

    def format_code(self, code: str) -> str:
        try:
            import black
            return black.format_str(code, mode=black.FileMode())
        except ImportError:
            return code  # 如果 black 不可用，返回原始代码

    def add_error_handling(self, code: str) -> str:
        lines = code.split('\n')
        indented_lines = [line for line in lines if line.strip() and line[0].isspace()]
        if indented_lines:
            indent = len(indented_lines[0]) - len(indented_lines[0].lstrip())
        else:
            indent = 4  # 默认缩进

        wrapped_code = f"""
try:
{' ' * indent}{code.replace(chr(10), chr(10) + ' ' * indent)}
except Exception as e:
{' ' * indent}print(f"执行过程中发生错误: {{str(e)}}")
{' ' * indent}raise
"""
        return wrapped_code.strip()

    def generate_docstring(self, code: str) -> str:
        prompt = f"""
        为以下 Python 代码生成一个简洁的文档字符串（docstring）：

        {code}

        docstring 应该简要说明代码的功能、输入和输出（如果有的话）。
        只返回生成的 docstring，不需要其他解释。
        """
        response = self.llm_client.one_chat(prompt)
        return response.strip()

    def enhance_code(self, code: str) -> str:
        formatted_code = self.format_code(code)
        error_handled_code = self.add_error_handling(formatted_code)
        docstring = self.generate_docstring(error_handled_code)
        
        # 在代码的开头插入 docstring
        code_lines = error_handled_code.split('\n')
        insert_position = next((i for i, line in enumerate(code_lines) if not line.strip().startswith('#')), 0)
        code_lines.insert(insert_position, f'"""{docstring}"""')
        
        return '\n'.join(code_lines)

class CodeExecutor:
    def __init__(self, code_runner: SSECodeRunner):
        self.code_runner = code_runner

    def execute_data_retrieval(self, code: str, step: Dict[str, Any], global_vars: Dict[str, Any]) -> Generator[Dict[str, Any], None, None]:
        for event in self.code_runner.run_sse(code, global_vars):
            if event['type'] == 'output':
                yield {"type": "code_execution", "content": event['content']}
            elif event['type'] == 'error':
                yield {"type": "error", "content": event['content']}
                raise Exception(event['content'])
            elif event['type'] == 'variables':
                updated_vars = event['content']
                if step['save_data_to'] in updated_vars:
                    data = updated_vars[step['save_data_to']]
                    yield {"type": "code_execution", "content": f"数据已保存到 {step['save_data_to']}"}
                    return data
                else:
                    error_msg = f"执行代码未产生预期的 '{step['save_data_to']}' 变量。可用变量: {list(updated_vars.keys())}"
                    yield {"type": "error", "content": error_msg}
                    raise Exception(error_msg)

    def execute_data_analysis(self, code: str, step: Dict[str, Any], global_vars: Dict[str, Any]) -> Generator[Dict[str, Any], None, None]:
        for event in self.code_runner.run_sse(code, global_vars):
            if event['type'] == 'output':
                yield {"type": "code_execution", "content": event['content']}
            elif event['type'] == 'error':
                yield {"type": "error", "content": event['content']}
                raise Exception(event['content'])
            elif event['type'] == 'variables':
                updated_vars = event['content']
                if 'analysis_result' in updated_vars:
                    result = updated_vars['analysis_result']
                    yield {"type": "code_execution", "content": "分析结果已生成"}
                    return result
                else:
                    error_msg = f"执行代码未产生预期的 'analysis_result' 变量。可用变量: {list(updated_vars.keys())}"
                    yield {"type": "error", "content": error_msg}
                    raise Exception(error_msg)
                
class ReportGenerator:
    def __init__(self, llm_client: LLMApiClient):
        self.llm_client = llm_client

    def generate_report(self, initial_query: str, analysis_results: List[Dict[str, str]]) -> Generator[Dict[str, Any], None, None]:
        prompt = self._create_report_prompt(initial_query, analysis_results)
        for chunk in self.llm_client.text_chat(prompt, is_stream=True):
            yield {"type": "report", "content": chunk}

    def _create_report_prompt(self, initial_query: str, analysis_results: List[Dict[str, str]]) -> str:
        results_summary = "\n\n".join([
            f"任务: {result['task']}\n结果: {result['result']}"
            for result in analysis_results
        ])
        return f"""
        基于以下初始查询和分析结果，生成一份全面的报告：

        初始查询：
        {initial_query}

        分析结果：
        {results_summary}

        请生成一份全面的报告，总结数据分析的发现和洞察。报告应该：
        1. 回答初始查询
        2. 总结每个分析任务的主要发现
        3. 提供整体的见解和结论
        4. 指出任何有趣或意外的发现
        5. 如果适用，提供进一步分析的建议

        报告应结构清晰、表述明确，并提供有意义的结论。
        """

class AkshareFunPlanner(SSEPlanner):
    def __init__(self, max_retry=8, allow_yfinance: bool = False):
        self.llm_factory = LLMFactory()
        self.llm_client = self.llm_factory.get_instance()
        self.code_runner = SSECodeRunner()
        self.data_summarizer = DataSummarizer()
        self.retriever = self.get_retrieval_provider()
        self.plan_manager = PlanManager()
        self.code_generator = CodeGenerator(self.llm_client, self.retriever)
        self.code_executor = CodeExecutor(self.code_runner)
        self.report_generator = ReportGenerator(self.llm_client)
        self.max_retry = max_retry
        self.allow_yfinance = allow_yfinance
        self.step_codes = {}
        self.step_vars = {
            "llm_factory": self.llm_factory,
            "code_runner": self.code_runner,
            "data_summarizer": self.data_summarizer
        }

    def plan_chat(self, query: str) -> Generator[Dict[str, Any], None, None]:
        if self.plan_manager.current_plan is None:
            plan = self.plan_manager.create_plan(query, self.retriever.get_categories())
        else:
            plan = self.plan_manager.modify_plan(query)
        
        yield {"type": "plan", "content": plan}
        yield {"type": "message", "content": "计划生成完毕。请检查计划并输入'确认计划'来开始执行，或继续修改计划。"}

    def execute_plan(self) -> Generator[Dict[str, Any], None, None]:
        if not self.plan_manager.is_plan_confirmed:
            yield {"type": "error", "content": "计划尚未确认。请先确认计划。"}
            return

        while not self.plan_manager.is_plan_complete():
            step = self.plan_manager.get_current_step()
            yield {"type": "progress", "content": {
                "step": self.plan_manager.current_step + 1,
                "total_steps": self.plan_manager.total_steps,
                "description": step['description'],
                "progress": (self.plan_manager.current_step + 1) / self.plan_manager.total_steps
            }}
            yield from self.execute_step(step)

        yield from self.get_final_report()

    def execute_step(self, step: Dict[str, Any]) -> Generator[Dict[str, Any], None, None]:
        code_generator = self.code_generator.generate_data_retrieval_code(step) if step['type'] == 'data_retrieval' else self.code_generator.generate_data_analysis_code(step, self.get_data_summaries(), self.allow_yfinance)
        
        code = "".join(chunk for chunk in code_generator if isinstance(chunk, str))
        yield {"type": "code_generation", "content": code}

        for attempt in range(self.max_retry):
            try:
                executor = self.code_executor.execute_data_retrieval if step['type'] == 'data_retrieval' else self.code_executor.execute_data_analysis
                result = yield from executor(code, step, self.step_vars)
                self.step_codes[self.plan_manager.current_step] = code
                self.plan_manager.add_execution_result({
                    "step": self.plan_manager.current_step,
                    "type": step['type'],
                    "result": result
                })
                break
            except Exception as e:
                if attempt < self.max_retry - 1:
                    yield {"type": "code_fix", "content": f"第 {attempt + 1} 次尝试失败。错误：{str(e)}。正在尝试修复代码。"}
                    code = "".join(chunk for chunk in self.code_generator.fix_code(code, str(e)) if isinstance(chunk, str))
                else:
                    yield {"type": "error", "content": f"在 {self.max_retry} 次尝试后仍无法执行代码。最后的错误：{str(e)}"}

        self.plan_manager.next_step()

    def get_final_report(self) -> Generator[Dict[str, Any], None, None]:
        yield from self.report_generator.generate_report(
            self.plan_manager.current_plan['query_summary'],
            self.plan_manager.execution_results
        )
        self._save_code_after_report()
        self.reset()
        yield {"type": "finished", "content": "报告已生成，计划已重置。可以重新开始新的任务啦！"}

    def reset(self) -> None:
        self.plan_manager = PlanManager()
        self.step_codes = {}
        self.step_vars = {
            "llm_factory": self.llm_factory,
            "code_runner": self.code_runner,
            "data_summarizer": self.data_summarizer
        }

    def get_data_summaries(self) -> Dict[str, str]:
        return {key: value for key, value in self.step_vars.items() if key.endswith('_summary')}

    def _save_code_after_report(self):
        # 实现代码保存逻辑
        pass

    # 其他辅助方法...