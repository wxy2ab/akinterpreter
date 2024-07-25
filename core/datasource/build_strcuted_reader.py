from typing import List, Dict, Any, Union, Callable
from abc import ABC, abstractmethod
import re
import inspect
import traceback

from core.llms._llm_api_client import LLMApiClient

class BuildStructedReader:
    def __init__(self, llm_client: LLMApiClient):
        self.llm_client = llm_client

    def build(self, cleaned_html: str) -> 'StructedReader':
        functions = self._generate_functions(cleaned_html)
        explanation = self._generate_explanation(functions)
        return StructedReader(functions, explanation, self)

    def _generate_functions(self, cleaned_html: str) -> List[Dict[str, Any]]:
        prompt = f"""
        分析以下已清理的HTML内容，并生成适当的Python函数来提取其中的结构化信息。请根据页面的具体内容和结构来决定应该生成哪些函数。不需要限制函数的数量，而应该根据页面的复杂度和内容来决定。

        以下是一些可能的函数示例，请根据实际内容进行调整：

        1. 如果页面主要是一篇文章：
           def get_article_markdown() -> str:
               # 返回文章的Markdown格式内容

        2. 如果页面包含数据表格：
           def get_xxx_table() -> pd.DataFrame:
               # 返回表格数据作为pandas DataFrame

        3. 如果页面包含多个数据块：
           def get_data_block_1() -> Dict[str, Any]:
               # 返回第一个数据块的信息
           def get_data_block_2() -> Dict[str, Any]:
               # 返回第二个数据块的信息
           # ... 根据需要添加更多函数

        4. 如果页面有导航目录：
           def get_nav() -> List[Dict[str, str]]:
               # 返回导航目录的结构
           def get_doc(url: str) -> str:
               # 获取目录中指定URL的页面内容

        5. 如果页面包含特定的结构化数据（如股票信息、天气数据等）：
           def get_specific_data() -> Dict[str, Any]:
               # 返回特定的结构化数据

        请根据以下HTML内容设计合适的函数：

        已清理的HTML:
        {cleaned_html[:2000]}  # 发送前2000个字符作为示例

        请以Python函数的形式返回你的建议，每个函数都应该包含简短的注释来解释其功能。确保函数能够处理可能的异常情况，并在必要时使用try-except块。
        """
        
        response = self.llm_client.text_chat(prompt)
        functions = self._parse_functions(response)
        return functions

    def _parse_functions(self, response: str) -> List[Dict[str, Any]]:
        function_pattern = r'def (\w+)\(.*?\):\n(.*?)(?=\ndef|\Z)'
        matches = re.finditer(function_pattern, response, re.DOTALL)
        
        functions = []
        for match in matches:
            function_name = match.group(1)
            function_body = match.group(2).strip()
            functions.append({
                'name': function_name,
                'body': function_body
            })
        
        return functions

    def _generate_explanation(self, functions: List[Dict[str, Any]]) -> str:
        function_names = [f['name'] for f in functions]
        prompt = f"""
        给定以下StructedReader的函数名列表:
        {function_names}

        请生成一个简明的说明，解释如何使用这些函数从网页中提取结构化信息。这个说明应该清晰易懂，使语言模型能够理解并有效地使用这些函数。请特别注意解释每个函数的用途和它们如何协同工作来全面解析页面内容。
        """
        
        explanation = self.llm_client.text_chat(prompt)
        return explanation

    def fix_code(self, func_or_code: Union[Callable, str], error_message: str) -> str:
        if callable(func_or_code):
            function_name = func_or_code.__name__
            function_body = inspect.getsource(func_or_code)
        elif isinstance(func_or_code, str):
            # 假设传入的是整个函数定义的字符串
            match = re.match(r'def (\w+)', func_or_code)
            if match:
                function_name = match.group(1)
                function_body = func_or_code
            else:
                raise ValueError("无法从提供的代码字符串中提取函数名")
        else:
            raise TypeError("func_or_code 必须是一个可调用对象或字符串")

        prompt = f"""
        以下是一个名为 {function_name} 的Python函数，在执行过程中出现了错误。请分析错误信息并提供修正后的代码。

        原始函数:
        ```python
        {function_body}
        ```

        错误信息:
        {error_message}

        请提供修正后的完整函数代码，确保处理可能的异常情况，并在必要时使用try-except块。请解释你所做的更改。
        """

        response = self.llm_client.text_chat(prompt)
        
        # 提取修正后的函数代码
        fixed_function_match = re.search(r'```python\n(def.*?)\n```', response, re.DOTALL)
        if fixed_function_match:
            fixed_function = fixed_function_match.group(1)
            return fixed_function
        else:
            return "无法生成修正后的代码。请检查LLM的响应。"

class StructedReader:
    def __init__(self, functions: List[Dict[str, Any]], explanation: str, builder: BuildStructedReader):
        self.functions = functions
        self.explanation = explanation
        self.builder = builder

    def get_functions(self) -> List[Dict[str, Any]]:
        return self.functions

    def get_explanation(self) -> str:
        return self.explanation

    def execute_function(self, function_name: str, *args, **kwargs):
        function_dict = next((f for f in self.functions if f['name'] == function_name), None)
        if not function_dict:
            raise ValueError(f"Function {function_name} not found")

        try:
            # 动态编译并执行函数
            exec(function_dict['body'], globals())
            return globals()[function_name](*args, **kwargs)
        except Exception as e:
            error_message = traceback.format_exc()
            print(f"Error executing {function_name}: {error_message}")
            
            # 尝试修复代码
            fixed_function = self.builder.fix_code(function_dict['body'], error_message)
            
            # 更新函数体
            function_dict['body'] = fixed_function
            
            # 重新尝试执行修复后的函数
            try:
                exec(fixed_function, globals())
                return globals()[function_name](*args, **kwargs)
            except Exception as e:
                print(f"Error executing fixed function {function_name}: {str(e)}")
                raise

    def __str__(self) -> str:
        return f"StructedReader 包含 {len(self.functions)} 个函数:\n" + \
               "\n".join(f"- {func['name']}" for func in self.functions) + \
               f"\n\n使用说明:\n{self.explanation}"