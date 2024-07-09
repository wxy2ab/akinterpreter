from datetime import datetime
import os
import re
from ..akshare_doc.akshare_data_singleton import AKShareDataSingleton
from typing import List, Dict, Tuple, Union
import json
from typing import Generator, Dict, Any, List, Optional
from ..llms.llm_factory import LLMFactory
from ..llms._llm_api_client import LLMApiClient
from ..interpreter.code_runner import CodeRunner
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

class AkshareSSEPlanner(SSEPlanner):
    def __init__(self,max_retry=6,allow_yfinance:bool=False):
        self.llm_factory = LLMFactory()
        self.llm_client: LLMApiClient = self.llm_factory.get_instance()
        self.code_runner = CodeRunner()
        self.data_summarizer = DataSummarizer()
        self.retriever = self.get_retrieval_provider()
        self.reset()
        self.prompts = AksharePrompts()
        self.max_retry = max_retry
        self.allow_yfinance = allow_yfinance
        self.step_codes = {} 

    def get_new_llm_client(self) -> LLMApiClient:
        return self.llm_factory.get_instance()
    
    def get_retrieval_provider(self) -> RetrievalProvider:
        return AkshareRetrievalProvider()

    def plan_chat(self, query: str) -> Generator[Dict[str, Any], None, None]:
        confirm_keywords = ["确认计划", "确认", "开始", "开始执行", "运行", "执行", "没问题", "没问题了"]
        reset_keywords = ["重来", "清除", "再来一次"]

        if query.lower() in reset_keywords:
            self.reset()
            yield {"type": "message", "content": "已重置所有数据，请重新开始。"}
            return

        if query.lower() in confirm_keywords:
            if not self.current_plan:
                yield {"type": "error", "content": "没有可确认的计划。请先创建一个计划。"}
                return
            yield from self.handle_confirm_plan()
            return

        prompt = self._create_plan_prompt(query) if self.current_plan is None else self._create_modify_plan_prompt(query)
        
        plan_text = ""
        for chunk in self.llm_client.text_chat(prompt, is_stream=True):
            plan_text += chunk
            yield {"type": "plan", "content": chunk}
        
        try:
            plan = self._extract_json_from_text(plan_text)
            self.current_plan = plan
            self.total_steps = len(self.current_plan['steps'])
            yield {"type": "plan", "content": self.current_plan}
            yield {"type": "message", "content": "计划生成完毕。请检查计划并输入'确认计划'来开始执行，或继续修改计划。"}
        except json.JSONDecodeError:
            yield {"type": "error", "content": "无法创建有效的计划。请重试。"}

    def _create_plan_prompt(self, query: str) -> str:
        categories = self.retriever.get_categories()
        return self.prompts.create_plan_prompt(query, categories)

    def _create_modify_plan_prompt(self, query: str) -> str:
        return self.prompts.modify_plan_prompt(query, self.current_plan)

    def _extract_json_from_text(self, text: str) -> Dict[str, Any]:
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            json_str = json_match.group()
            return json.loads(json_str)
        raise json.JSONDecodeError("No valid JSON found in the text", text, 0)

    def handle_confirm_plan(self) -> Generator[Dict[str, Any], None, None]:
        if not self.current_plan:
            yield {"type": "error", "content": "没有可确认的计划。请先创建一个计划。"}
            return

        self.confirm_plan()
        yield {"type": "message", "content": "计划已确认。开始执行计划。"}
        yield from self.execute_plan()

    def confirm_plan(self) -> None:
        if not self.current_plan:
            raise ValueError("没有可确认的计划。请先创建一个计划。")
        self.current_step = 0
        self.is_plan_confirmed = True

    def execute_plan(self) -> Generator[Dict[str, Any], None, None]:
        if not self.is_plan_confirmed:
            yield {"type": "error", "content": "计划尚未确认。请先确认计划。"}
            return

        yield from self.stream_progress()

    def step(self) -> Generator[Dict[str, Any], None, None]:
        if not self.current_plan:
            yield {"type": "error", "content": "没有可用的计划。请先创建并确认一个计划。"}
            return

        if self.current_step >= len(self.current_plan['steps']):
            yield {"type": "message", "content": "所有步骤已完成。"}
            return

        current_step = self.current_plan['steps'][self.current_step]
        yield {"type": "message", "content": f"执行步骤 {self.current_step + 1}: {current_step['description']}"}

        code_generator = self._generate_code(current_step)
        full_code = ""
        for code_chunk in code_generator:
            if isinstance(code_chunk, dict) and code_chunk["type"] == "code_generation_progress":
                yield code_chunk
            elif isinstance(code_chunk, str):
                full_code += code_chunk

        if not full_code:
            yield {"type": "error", "content": "未能生成有效的代码。"}
            return

        yield {"type": "code_generation", "content": full_code}

        max_attempts = self.max_retry
        for attempt in range(max_attempts):
            try:
                if current_step['type'] == 'data_retrieval':
                    # 对于数据检索任务
                    result = self.execute_code(full_code)
                    if current_step['save_data_to'] in result['variables']:
                        self.step_vars[current_step['save_data_to']] = result['variables'][current_step['save_data_to']]
                        yield {"type": "code_execution", "content": f"数据已保存到 {current_step['save_data_to']}"}
                        self.step_codes[self.current_step] = full_code  # 保存成功的代码
                    else:
                        raise Exception(f"执行代码未产生预期的 '{current_step['save_data_to']}' 变量")
                elif current_step['type'] == 'data_analysis':
                    # 对于数据分析任务
                    result = self.execute_code(full_code)
                    if 'analysis_result' in result['variables']:
                        self.step_vars[f"analysis_result_{self.current_step}"] = result['variables']['analysis_result']
                        yield {"type": "code_execution", "content": "分析结果已生成"}
                        self.step_codes[self.current_step] = full_code  # 保存成功的代码
                    else:
                        raise Exception("执行代码未产生预期的 'analysis_result' 变量")
                else:
                    raise Exception(f"未知的步骤类型: {current_step['type']}")

                self.execution_results.append({"step": self.current_step, "result": result})
                break
            except Exception as e:
                if attempt < max_attempts - 1:
                    yield {"type": "code_fix", "content": f"第 {attempt + 1} 次尝试失败。错误：{str(e)}。正在尝试修复代码。"}
                    fix_generator = self._fix_code(full_code, str(e))
                    full_code = "".join(chunk for chunk in fix_generator if isinstance(chunk, str))
                else:
                    yield {"type": "error", "content": f"在 {max_attempts} 次尝试后仍无法执行代码。最后的错误：{str(e)}"}

        self.current_step += 1

    def execute_code(self, code: str) -> Dict[str, Any]:
        global_vars = self.step_vars.copy()
        global_vars['llm_client'] = self.get_new_llm_client()  # 为每次执行提供新的 LLMApiClient 实例
        output, error = self.code_runner.run(code, global_vars)
        if error:
            raise Exception(error)
        return {"output": output, "variables": global_vars}

    def stream_progress(self) -> Generator[Dict[str, Any], None, None]:
        while self.current_step < self.total_steps:
            yield {
                "type": "progress",
                "content": {
                    "step": self.current_step + 1,
                    "total_steps": self.total_steps,
                    "description": self.current_plan['steps'][self.current_step]['description'],
                    "progress": (self.current_step + 1) / self.total_steps
                }
            }
            yield from self.step()

        yield from self.get_final_report()

    def get_final_report(self) -> Generator[Dict[str, Any], None, None]:
        if not self.execution_results:
            yield {"type": "message", "content": "没有可报告的结果。请先执行计划。"}
            return

        prompt = self._create_report_prompt()
        for chunk in self.llm_client.text_chat(prompt, is_stream=True):
            yield {"type": "report", "content": chunk}

    def handle_error(self, error: Exception) -> Generator[Dict[str, Any], None, None]:
        error_message = str(error)
        yield {"type": "error", "content": error_message}
        
        fix_prompt = f"发生了一个错误：{error_message}。请提供解决方案或下一步建议。"
        for chunk in self.llm_client.text_chat(fix_prompt, is_stream=True):
            yield {"type": "solution", "content": chunk}

    def save_state(self) -> Dict[str, Any]:
        return {
            "current_plan": self.current_plan,
            "execution_results": self.execution_results,
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "is_plan_confirmed": self.is_plan_confirmed
        }

    def load_state(self, state: Dict[str, Any]) -> None:
        self.current_plan = state.get("current_plan")
        self.execution_results = state.get("execution_results", [])
        self.current_step = state.get("current_step", 0)
        self.total_steps = state.get("total_steps", 0)
        self.is_plan_confirmed = state.get("is_plan_confirmed", False)

    def _generate_code(self, step: Dict[str, Any]) -> Generator[Union[Dict[str, Any], str], None, None]:
        if step['type'] == 'data_retrieval':
            yield from self._generate_data_retrieval_code(step)
        elif step['type'] == 'data_analysis':
            yield from self._generate_data_analysis_code(step)
        else:
            yield {"type": "error", "content": f"错误：未知的步骤类型 {step['type']}"}

    def _generate_data_retrieval_code(self, step: Dict[str, Any]) -> Generator[Union[Dict[str, Any], str], None, None]:
        category = step['data_category']
        
        # 从选定类别中选择函数
        selected_functions = yield from self._select_functions_from_category(step, category)
        
        # 生成代码
        extracted_code = ""
        for item in self._generate_code_for_functions(step, selected_functions):
            if isinstance(item, dict):
                yield item  # 传递进度信息
            elif isinstance(item, str):
                extracted_code = item  # 保存提取的代码
        
        # yield 最终的代码
        yield extracted_code

    def _extract_code(self, content: str) -> str:
        # 使用正则表达式提取代码块
        code_match = re.search(r'```python(.*?)```', content, re.DOTALL)
        if code_match:
            return code_match.group(1).strip()
        else:
            # 如果没有找到代码块，返回整个内容（假设整个内容都是代码）
            return content.strip()

    def _generate_code_for_functions(self, step: Dict[str, Any], functions: List[str]) -> Generator[Union[Dict[str, Any], str], None, None]:
        function_docs = self.retriever.get_specific_doc(functions)

        code_prompt = self.prompts.generate_code_for_functions_prompt(step, function_docs)

        llm_client = self.get_new_llm_client()
        full_content = ""
        for chunk in llm_client.text_chat(code_prompt, is_stream=True):
            full_content += chunk
            yield {"type": "code_generation_progress", "content": chunk}
        
        # 提取代码块
        extracted_code = self._extract_code(full_content)
        
        # 首先yield完整的生成内容
        yield {"type": "code_generation", "content": full_content}
        
        # 然后yield提取出的代码
        yield extracted_code

    def _select_data_category(self, step: Dict[str, Any], categories: Dict[str, str]) -> Generator[str, None, None]:
        category_prompt = self.prompts.select_data_category_prompt(step, categories)
        
        llm_client = self.get_new_llm_client()
        response = yield from llm_client.text_chat(category_prompt, is_stream=True)
        selected_category = response.strip()
        yield {"type": "category_selection", "content": f"已选择数据类别：{selected_category}"}
        return selected_category

    def _select_functions_from_category(self, step: Dict[str, Any], category: str) -> Generator[List[str], None, None]:
        functions = self.retriever.get_functions([category])
        function_prompt = self.prompts.select_functions_from_category_prompt(step, functions[category])
        
        llm_client = self.get_new_llm_client()
        full_response = ""
        for chunk in llm_client.text_chat(function_prompt, is_stream=True):
            full_response += chunk
            yield {"type": "function_selection_progress", "content": chunk}

        selected_functions = [func.strip() for func in full_response.split(',')]
        yield {"type": "function_selection", "content": f"已选择函数：{', '.join(selected_functions)}"}
        return selected_functions

    def _generate_data_analysis_code(self, step: Dict[str, Any]) -> Generator[Union[Dict[str, Any], str], None, None]:
        data_summaries = {
            data_var: self.step_vars.get(f"{data_var}_summary", "数据摘要不可用")
            for data_var in step['required_data']
        }
        
        code_prompt = self.prompts.generate_data_analysis_code_prompt(step, data_summaries,self.allow_yfinance)

        llm_client = self.get_new_llm_client()
        full_code = ""
        for chunk in llm_client.text_chat(code_prompt, is_stream=True):
            full_code += chunk
            yield {"type": "code_generation_progress", "content": chunk}
        
        code = self._extract_code(full_code)
        yield code

    def _fix_code(self, code: str, error: str) -> Generator[str, None, None]:
        fix_prompt = self.prompts.fix_code_prompt(code, error)
        full_code = ""
        for chunk in self.llm_client.text_chat(fix_prompt, is_stream=True):
            full_code += chunk
            yield {"type": "code_fix_progress", "content": chunk}
        
        fixed_code = self._extract_code(full_code)
        yield fixed_code

    def reset(self) -> None:
        self.current_step = 0
        self.total_steps = 0
        self.is_plan_confirmed = False
        self.current_plan = None
        self.execution_results = []
        self.step_codes = {}
        self.step_vars: Dict[str, Any] = {
            "llm_factory": self.llm_factory,
            "code_runner": self.code_runner,
            "data_summarizer": self.data_summarizer
        }

    def get_final_report(self) -> Generator[Dict[str, Any], None, None]:
        if not self.execution_results:
            yield {"type": "message", "content": "没有可报告的结果。请先执行计划。"}
            return

        # 收集所有分析结果
        analysis_results = []
        for step in self.current_plan['steps']:
            if step['type'] == 'data_analysis':
                result_key = f"analysis_result_{step['step_number']}"
                if result_key in self.step_vars:
                    analysis_results.append({
                        "task": step['description'],
                        "result": self.step_vars[result_key]
                    })

        prompt = self._create_report_prompt(analysis_results)
        for chunk in self.llm_client.text_chat(prompt, is_stream=True):
            yield {"type": "report", "content": chunk}

        saved = self._save_code_after_report()
        yield saved
        self.reset()
        yield {"type": "finished", "content": "查询已完成，已重置所有数据。可以开始新的查啦。"}

    def _save_code_after_report(self):
        # 确保输出目录存在
        os.makedirs("output/succeed", exist_ok=True)

        # 生成文件名
        query_summary = self._generate_query_summary()
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"output/succeed/{query_summary}_{timestamp}.json"

        # 保存代码
        self.save_to_file(filename)
        
        return {"type": "message", "content": f"代码已保存到 {filename}"}

    def _generate_query_summary(self) -> str:
        # 使用 LLM 生成查询总结
        query = self.current_plan.get('query_summary', '未知查询')
        prompt = f"请将以下查询总结为4-6个字的简短描述：\n{query}"
        response = self.llm_client.one_chat(prompt)
        
        # 清理响应，确保它是一个有效的文件名
        summary = ''.join(c for c in response if c.isalnum() or c in ('-', '_'))
        return summary[:20]  # 限制长度为20个字符

    def _create_report_prompt(self, analysis_results: List[Dict[str, str]]) -> str:
        initial_query = self.current_plan.get('initial_query', '未提供初始查询')
        
        results_summary = "\n\n".join([
            f"任务: {result['task']}\n结果: {result['result']}"
            for result in analysis_results
        ])

        return self.prompts.create_report_prompt(initial_query, results_summary)

    def save_to_file(self, filename: str):
        """保存计划和代码到文件"""
        data = {
            "current_plan": self.current_plan,
            "step_codes": self.step_codes,
            "allow_yfinance": self.allow_yfinance
        }
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @classmethod
    def load_from_file(cls, filename: str):
        """从文件加载计划和代码"""
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        planner = cls(allow_yfinance=data.get('allow_yfinance', False))
        planner.current_plan = data['current_plan']
        planner.step_codes = data['step_codes']
        return planner

    def replay(self) -> Generator[Dict[str, Any], None, None]:
        """重放已保存的计划和代码"""
        if not self.current_plan or not self.step_codes:
            yield {"type": "error", "content": "没有可重放的计划或代码。"}
            return

        self.reset()
        self.is_plan_confirmed = True

        for step in self.current_plan['steps']:
            self.current_step = step['step_number'] - 1  # step_number 是从1开始的
            yield {"type": "message", "content": f"执行步骤 {step['step_number']}: {step['description']}"}

            if str(self.current_step) in self.step_codes:
                code = self.step_codes[str(self.current_step)]
                try:
                    result = self.execute_code(code)
                    if step['type'] == 'data_retrieval':
                        self.step_vars[step['save_data_to']] = result['variables'][step['save_data_to']]
                        yield {"type": "code_execution", "content": f"数据已保存到 {step['save_data_to']}"}
                    elif step['type'] == 'data_analysis':
                        self.step_vars[f"analysis_result_{self.current_step}"] = result['variables']['analysis_result']
                        yield {"type": "code_execution", "content": "分析结果已生成"}
                    
                    self.execution_results.append({"step": self.current_step, "result": result})
                except Exception as e:
                    yield {"type": "error", "content": f"重放步骤 {step['step_number']} 时出错: {str(e)}"}
            else:
                yield {"type": "error", "content": f"步骤 {step['step_number']} 没有对应的代码。"}

        yield {"type": "message", "content": "重放完成。"}