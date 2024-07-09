import os
from typing import Any, Tuple, Union, Dict, List, Generator, Iterator
from ._sse_interpreter import SSEInterpreter
from ..llms._llm_api_client import LLMApiClient
from ..llms.llm_factory import LLMFactory
from .data_summarizer import DataSummarizer
from .code_runner import CodeRunner

class SSEDataInterpreter(SSEInterpreter):
    def __init__(self, max_retries=3, is_debug=False):
        self.is_debug = is_debug
        factory = LLMFactory()
        self.llm_client: LLMApiClient = factory.get_instance()
        self.code_runner = CodeRunner()
        self.max_retries = max_retries
        self.pre_installed_libraries = ["pandas", "numpy", "matplotlib", "seaborn", "scipy", "sklearn", "mplfinance"]
        self.output_dir = "output"
        self.figure_dir = os.path.join(self.output_dir, "figures")
        self.data_dir = os.path.join(self.output_dir, "data")
        os.makedirs(self.figure_dir, exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)

    def interpret(self, data: Any, user_request: str, is_stream: bool = False) -> Union[Tuple[str, str], Generator[str, None, None]]:
        self.data = data
        self.data_summary = DataSummarizer.get_data_summary(data)
        self.user_request = user_request
        self.llm_client.clear_chat()

        if is_stream:
            return self._stream_interpret()
        else:
            return self._non_stream_interpret()

    def _stream_interpret(self) -> Generator[str, None, None]:
        code_generator = self.generate_code(self.data, self.user_request, is_stream=True)
        code = ""
        for chunk in code_generator:
            yield chunk
            code += chunk
        
        code = self._extract_code(code)  # Extract the final code from the accumulated response
        yield f"\n最终代码:\n{code}\n"
        
        for attempt in range(self.max_retries):
            yield f"运行代码 (尝试第 {attempt + 1}) 次...\n"
            output, error = self.execute_code(code, self.data)
            
            if not error:
                yield "代码执行成功.\n"
                break
            
            yield f"Execution failed. Error: {error}\n"
            
            if attempt < self.max_retries - 1:
                yield f"第{attempt + 1}次尝试失败. 尝试更正代码...\n"
                code = yield from self.fix_code(code, error)
            else:
                yield f"所有 {self.max_retries} 次尝试失败. 无法更正代码.\n"
        
        yield from self.generate_report(output, error, self.user_request, is_stream=True)

    def _stream_generate_code(self, prompt: str) -> Generator[str, None, None]:
        response_stream = self.llm_client.text_chat(prompt, is_stream=True)
        accumulated_code = ""
        for chunk in response_stream:
            accumulated_code += chunk
            yield chunk
        
        extracted_code = self._extract_code(accumulated_code)
        yield f"\nExtracted code:\n{extracted_code}"
        return extracted_code
    
    def _non_stream_interpret(self) -> Tuple[str, str]:
        code = self.generate_code(self.data, self.user_request)
        
        for attempt in range(self.max_retries):
            output, error = self.execute_code(code)
            
            if not error:
                break
            
            if attempt < self.max_retries - 1:
                print(f"尝试 {attempt + 1} 失败。正在尝试修复代码...")
                code = self.fix_code(code, error)
            else:
                print(f"所有 {self.max_retries} 次尝试都失败了。无法修复代码。")
        
        report = self.generate_report(output, error, self.user_request)
        
        return code, report

    def generate_code(self, data: Any, user_request: str, is_stream: bool = False) -> Union[str, Generator[str, None, None]]:
        prompt = self._generate_code_prompt(user_request)
        if is_stream:
            return self._stream_llm_response(prompt)
        else:
            response = self.llm_client.text_chat(prompt)
            return self._extract_code(response)

    def generate_report(self, data: Any, error: Any, user_request: str, is_stream: bool = False) -> Union[str, Generator[str, None, None]]:
        figure_outputs, data_outputs = self._parse_outputs(data)
        prompt = self._generate_report_prompt(data, error, user_request, figure_outputs, data_outputs)
        
        if is_stream:
            return self._stream_llm_response(prompt)
        else:
            markdown_report = self.llm_client.text_chat(prompt)
            return self._correct_report_paths(markdown_report, figure_outputs, data_outputs)

    def fix_code(self, code: str, error: str) -> Union[str, Generator[str, None, None]]:
        prompt = self._generate_fix_code_prompt(code, error)
        if isinstance(code, Generator):
            return self._stream_llm_response(prompt)
        else:
            response = self.llm_client.text_chat(prompt)
            return self._extract_code(response)

    def execute_code(self, code: str, data: Any) -> Tuple[str, str]:
        return self.code_runner.run(code, {'data': data})

    def process_sse_event(self, event: Dict[str, Any]) -> str:
        if 'content' in event:
            return event['content']
        return ''

    def handle_tool_call(self, tool_call: Dict[str, Any], function_module: Any) -> str:
        function_name = tool_call.get('name', '')
        function_args = tool_call.get('arguments', {})
        
        if hasattr(function_module, function_name):
            function = getattr(function_module, function_name)
            try:
                result = function(**function_args)
                return f"Tool '{function_name}' result: {result}"
            except Exception as e:
                return f"Error executing '{function_name}': {str(e)}"
        else:
            return f"Function '{function_name}' not found in the provided module."

    def stream_processor(self, stream: Iterator[Dict[str, Any]]) -> Generator[str, None, None]:
        for event in stream:
            yield self.process_sse_event(event)

    def _generate_code_prompt(self, user_request: str) -> str:
        return f"""根据以下数据摘要和用户请求，生成Python代码来分析数据并满足请求。

数据摘要：
{self.data_summary}

用户请求：{user_request}

请生成能够完成用户请求的Python代码，基于提供的数据摘要。
遵循以下指导原则：

1. 您可以使用以下预安装的库：{', '.join(self.pre_installed_libraries)}。
2. 使用 'data' 变量访问输入的数据集。
3. 保存图形到：{self.figure_dir}
4. 保存数据文件到：{self.data_dir}
5. 使用 print('FIGURE_OUTPUT: <filename>, <description>') 来标记图形输出。
6. 使用 print('DATA_OUTPUT: <filename>, <description>') 来标记数据文件输出。

请提供完整的Python代码："""

    def _generate_report_prompt(self, data: str, error: Any, user_request: str, figure_outputs: List[str], data_outputs: List[str]) -> str:
        return f"""根据以下数据分析的输出和错误（如果有），提供一个全面的报告来解释结果，包括数据处理步骤、分析发现和创建的可视化。

输出：
{data}

错误：
{error}

原始用户请求：{user_request}

生成的图形：{figure_outputs}
生成的数据文件：{data_outputs}

请提供一个清晰简洁的报告，使用Markdown格式。"""

    def _generate_fix_code_prompt(self, code: str, error: str) -> str:
        return f"""之前的数据分析代码产生了一个错误。请修复它。

代码：
{code}

错误：
{error}

请提供修正后的代码版本，该版本应解决错误并仍然满足原始的数据分析请求。"""

    def _extract_code(self, response: str) -> str:
        import re
        code_blocks = re.findall(r'```(?:python)?(.*?)```', response, re.DOTALL)
        
        if code_blocks:
            code = code_blocks[0].strip()
            if  'data' in code:
                return code
            else:
                raise ValueError("Code block does not contain 'data' keyword.")
        else:
            return response.strip()

    def _parse_outputs(self, data: str) -> Tuple[List[str], List[str]]:
        figure_outputs = []
        data_outputs = []
        for line in data.split('\n'):
            if line.startswith('FIGURE_OUTPUT:'):
                figure_outputs.append(line.split(': ')[1])
            elif line.startswith('DATA_OUTPUT:'):
                data_outputs.append(line.split(': ')[1])
        return figure_outputs, data_outputs

    def _correct_report_paths(self, report: str, figure_outputs: List[str], data_outputs: List[str]) -> str:
        for output in figure_outputs:
            filename, description = output.split(', ')
            report = report.replace(f"path/to/{filename}", f"{self.figure_dir}/{filename}")
        
        for output in data_outputs:
            filename, description = output.split(', ')
            report = report.replace(f"path/to/{filename}", f"{self.data_dir}/{filename}")
        
        return report

    def _stream_llm_response(self, prompt: str) -> Generator[str, None, None]:
        response_stream = self.llm_client.text_chat(prompt, is_stream=True)
        for chunk in response_stream:
            yield chunk