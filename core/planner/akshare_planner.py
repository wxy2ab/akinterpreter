import inspect
import json
import re
import akshare as ak
from typing import Any, Dict, List, Optional, Tuple
from ..interpreter.data_interpreter import DataInterpreter
from ..interpreter.code_runner import CodeRunner
from ..interpreter._planner import Planner
from ..akshare_doc.akshare_data_singleton import AKShareDataSingleton
from ..llms._llm_api_client import LLMApiClient
from ..llms.llm_factory import LLMFactory
from ..interpreter.data_summarizer import DataSummarizer

class AkshareInterpreterPlanner(Planner):
    def __init__(self, max_retries=6):
        factory = LLMFactory()
        self.llm_client: LLMApiClient = factory.get_instance()
        self.data_interpreter = DataInterpreter(max_retries=10)
        self.code_runner = CodeRunner()
        self.data_singleton = AKShareDataSingleton()
        self.classified_functions = self.data_singleton.get_classified_functions()
        self.akshare_docs = self.data_singleton.get_akshare_docs()
        self.category_summaries = self.data_singleton.get_category_summaries()
        self.max_retries = max_retries
        self.current_plan = None

    def plan(self, user_requests: str) -> Dict[str, Any]:
        data_retrieval_query, data_analysis_query = self._split_query(user_requests)
        selected_categories = self._select_categories(data_retrieval_query)
        selected_functions = self._select_functions(data_retrieval_query, selected_categories)
        
        self.current_plan  =  {
            "data_retrieval_query": data_retrieval_query,
            "data_analysis_query": data_analysis_query,
            "selected_categories": selected_categories,
            "selected_functions": selected_functions
        }
        return self.current_plan

    def generate_code_for_data(self, data_retrieval_query: str, code: str = None, error: str = None) -> str:
        if code and error:
            return self._fix_data_retrieval_code(data_retrieval_query, code, error)
        
        if self.current_plan is None or self.current_plan["data_retrieval_query"] != data_retrieval_query:
            self.plan(data_retrieval_query)
        
        return self._generate_data_retrieval_code(
            self.current_plan["data_retrieval_query"], 
            self.current_plan["selected_functions"]
        )

    def execute_data_retrieval(self, code: str, global_vars: Dict[str, Any] = {}) -> Tuple[Any, str]:
        output, error = self.code_runner.run(code, global_vars)
        if 'result' in global_vars:
            return global_vars['result'], error
        else:
            return output, error

    def generate_code_for_report(self, data: Any, data_analysis_query: str, code: str = None, error: str = None) -> str:
        if code and error:
            return self._fix_data_analysis_code(data, data_analysis_query, code, error)
        return self.data_interpreter.generate_code(data, data_analysis_query)

    def execute_data_analysis(self, data: Any, code: str, global_vars: Dict[str, Any] = {}) -> Tuple[str, str]:
        global_vars['data'] = data
        output, error = self.code_runner.run(code, global_vars)
        return output, error

    def generate_code_for_report(self, data: Any, data_analysis_query: str, code: str = None, error: str = None) -> str:
        if code and error:
            return self._fix_data_analysis_code(data, data_analysis_query, code, error)
        return self.data_interpreter.generate_code(data, data_analysis_query)

    def generate_report(self, data: str, query: str) -> str:
        prompt = ChinesePrompts.generate_report_prompt(data, query)
        response = self.llm_client.text_chat(prompt)
        return response
    
    def plan_and_execute(self, user_requests: str, data: Any = None) -> Tuple[str, str]:
        self.plan(user_requests)  # 确保 current_plan 已经设置
        data_retrieval_code = self.generate_code_for_data(self.current_plan["data_retrieval_query"])
        
        # 数据检索循环
        global_vars = {}
        for attempt in range(self.max_retries):
            try:
                retrieved_data, error = self.execute_data_retrieval(data_retrieval_code, global_vars)
                if not error:
                    break
                data_retrieval_code = self.generate_code_for_data(
                    self.current_plan["data_retrieval_query"], 
                    data_retrieval_code, 
                    error
                )
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise ValueError(f"在 {self.max_retries} 次尝试后仍然无法检索数据: {str(e)}")
                print(f"数据检索尝试 {attempt + 1} 失败: {str(e)}. 重新生成代码...")
        
        if error:
            raise ValueError(f"在 {self.max_retries} 次尝试后仍然无法检索数据: {error}")

        # 数据分析循环
        analysis_code = self.generate_code_for_report(retrieved_data, self.current_plan["data_analysis_query"])
        for attempt in range(self.max_retries):
            try:
                analysis_output, error = self.execute_data_analysis(retrieved_data, analysis_code, global_vars)
                if not error:
                    break
                analysis_code = self.generate_code_for_report(
                    retrieved_data, 
                    self.current_plan["data_analysis_query"], 
                    analysis_code, 
                    error
                )
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise ValueError(f"在 {self.max_retries} 次尝试后仍然无法完成数据分析: {str(e)}")
                print(f"数据分析尝试 {attempt + 1} 失败: {str(e)}. 重新生成代码...")
        
        if error:
            raise ValueError(f"在 {self.max_retries} 次尝试后仍然无法完成数据分析: {error}")

        # 生成最终报告
        final_report = self.generate_report(analysis_output, self.current_plan["data_analysis_query"])

        return analysis_output, final_report

    def _fix_data_retrieval_code(self, data_retrieval_query: str, code: str, error: str) -> str:
        prompt = ChinesePrompts.fix_data_retrieval_code_prompt(data_retrieval_query, code, error)
        response = self.llm_client.text_chat(prompt)
        return self._extract_code(response)

    def _fix_data_analysis_code(self, data: Any, data_analysis_query: str, code: str, error: str) -> str:
        data_summary = DataSummarizer.get_data_summary(data)
        prompt = ChinesePrompts.fix_data_analysis_code_prompt(data_summary, data_analysis_query, code, error)
        response = self.llm_client.text_chat(prompt)
        return self._extract_code(response)

    def _split_query(self, query: str) -> Tuple[str, str]:
        prompt = ChinesePrompts.split_query_prompt(query)
        response = self.llm_client.text_chat(prompt)
        try:
            split_query = self._extract_json_from_response(response)
            return split_query["data_retrieval"], split_query["data_analysis"]
        except ValueError as e:
            raise ValueError(f"无法从 LLM 的响应中提取 JSON: {str(e)}")

    def _select_categories(self, data_retrieval_query: str) -> List[str]:
        prompt = ChinesePrompts.select_categories_prompt(data_retrieval_query, self.category_summaries)
        response = self.llm_client.text_chat(prompt)
        try:
            selected = self._extract_json_from_response(response)
            return selected["selected_categories"]
        except ValueError as e:
            raise ValueError(f"无法从 LLM 的类别选择响应中提取 JSON: {str(e)}")

    def _select_functions(self, data_retrieval_query: str, selected_categories: List[str]) -> List[str]:
        function_descriptions = []
        for category in selected_categories:
            function_descriptions.extend(self.classified_functions.get(category, []))

        prompt = ChinesePrompts.select_functions_prompt(data_retrieval_query, function_descriptions)
        response = self.llm_client.text_chat(prompt)
        try:
            selected = self._extract_json_from_response(response)
            return selected["selected_functions"]
        except ValueError as e:
            raise ValueError(f"无法从 LLM 的函数选择响应中提取 JSON: {str(e)}")

    def _generate_data_retrieval_code(self, data_retrieval_query: str, selected_functions: List[str]) -> str:
        function_docs = {func: self.read_akshare_doc(func) for func in selected_functions}
        prompt = ChinesePrompts.generate_data_retrieval_code_prompt(data_retrieval_query, function_docs)
        response = self.llm_client.text_chat(prompt)
        return self._extract_code(response)

    def _extract_code(self, response: str) -> str:
        code_blocks = re.findall(r'```(?:python)?(.*?)```', response, re.DOTALL)
        if code_blocks:
            return '\n'.join(block.strip() for block in code_blocks)

        lines = response.split('\n')
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

        return response.strip()

    def _execute_code(self, code: str) -> Tuple[Any, Optional[str]]:
        return self.code_runner.run(code, {})

    def _extract_json_from_response(self, response: str) -> Dict:
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                json_str = json_match.group()
                json_str = re.sub(r'\s+', ' ', json_str)
                json_str = json_str.replace('\\"', '"').replace("\\'", "'")
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    raise ValueError("无法解析找到的 JSON 字符串，即使在预处理后")
        else:
            raise ValueError("响应中没有找到有效的 JSON")

    def read_akshare_doc(self, func_name: str) -> str:
        if func_name in self.akshare_docs:
            return self.akshare_docs[func_name]
        
        func = getattr(ak, func_name, None)
        if func and callable(func):
            doc = inspect.getdoc(func)
            if doc:
                return doc
        
        return f"无法获取 {func_name} 的文档"
    

class ChinesePrompts:
    @staticmethod
    def split_query_prompt(query: str) -> str:
        return f"""
        请将以下查询拆分为两个部分：
        1. 数据获取部分：描述需要从 AKShare 获取哪些数据。
        2. 数据分析部分：描述如何分析和解释获取到的数据。

        查询: {query}

        请以 JSON 格式返回结果，包含 "data_retrieval" 和 "data_analysis" 两个键。
        """

    @staticmethod
    def select_categories_prompt(data_retrieval_query: str, category_summaries: dict) -> str:
        return f"""
        基于以下数据获取需求，从给定的 AKShare 数据类别中选择最相关的类别：

        需求: {data_retrieval_query}

        可用数据类别:
        {json.dumps(category_summaries, ensure_ascii=False, indent=2)}

        请选择 1-3 个最相关的类别，并以 JSON 格式返回结果，格式如下：
        {{"selected_categories": ["category1", "category2"]}}
        """

    @staticmethod
    def select_functions_prompt(data_retrieval_query: str, function_descriptions: list) -> str:
        return f"""
        基于以下数据获取需求，从给定的 AKShare 函数列表中选择最合适的函数：

        需求: {data_retrieval_query}

        可用函数:
        {json.dumps(function_descriptions, ensure_ascii=False, indent=2)}

        请选择 1-3 个最相关的函数，并以 JSON 格式返回结果，格式如下：
        {{"selected_functions": ["function_name1", "function_name2"]}}
        """

    @staticmethod
    def generate_data_retrieval_code_prompt(data_retrieval_query: str, function_docs: dict) -> str:
        return f"""
        根据以下数据获取需求和选定的 AKShare 函数，生成 Python 代码来获取数据：

        需求: {data_retrieval_query}

        选定的函数及其文档:
        {json.dumps(function_docs, ensure_ascii=False, indent=2)}

        请遵循以下规则生成代码：
        1. 导入必要的模块，主要是 akshare。不要遗漏导入，尤其是内置模块的导入，比如处理时间日期的datetime模块。
        2. 直接使用选定的 AKShare 函数来获取所需数据。
        3. 注意返回数据的数据类型，和函数参数数据类型，比如akshare返回和需要的日期基本都不是内置的datetime类型，是字符串。
        4. 将最终结果直接赋值给名为 'result' 的变量。确保 'result' 包含所有必要的数据，通常应该是一个或多个 DataFrame(多个DataFrame保存在字典之中返回)。
        5. 代码应该简洁明了，只包含必要的步骤来获取和处理数据。
        6. 仔细检查代码,确保代码是完整可执行的，并且能够返回所需的数据。
        7. 仔细阅读函数文档中的返回值说明，确保正确处理返回的数据结构。

        请直接提供完整的、可执行的 Python 代码，不要包含任何额外的解释或注释。
        """

    @staticmethod
    def fix_data_retrieval_code_prompt(data_retrieval_query: str, code: str, error: str) -> str:
        return f"""
        之前的数据检索代码产生了错误。请修复它。

        数据检索需求：
        {data_retrieval_query}

        代码：
        {code}

        错误：
        {error}

        请提供修正后的完整代码。确保代码是可执行的，并能够检索所需的数据。
        仅返回修正后的Python代码，不需要任何额外的解释。
        """

    @staticmethod
    def fix_data_analysis_code_prompt(data_summary: str, data_analysis_query: str, code: str, error: str) -> str:
        return f"""
        之前的数据分析代码产生了错误。请修复它。

        数据摘要：
        {data_summary}

        数据分析需求：
        {data_analysis_query}

        代码：
        {code}

        错误：
        {error}

        请提供修正后的完整代码。确保代码是可执行的，并能够完成所需的数据分析。
        仅返回修正后的Python代码，不需要任何额外的解释。
        """
    @staticmethod
    def generate_report_prompt(analysis_output: str, data_analysis_query: str) -> str:
        return f"""
        基于以下数据分析输出和原始查询，生成一份全面的报告：

        数据分析输出：
        {analysis_output}

        原始数据分析查询：
        {data_analysis_query}

        请提供一份详细的报告，包括以下内容：
        1. 数据分析的主要发现
        2. 对查询的直接回答
        3. 任何有趣的观察或洞见
        4. 可能的后续分析建议

        请使用清晰、专业的语言，并尽可能提供具体的数字和事实。
        """