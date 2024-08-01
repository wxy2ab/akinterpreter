import json
from typing import Generator, Dict, Any, List

from .llm_provider import LLMProvider
from ..planner.akshare_retrieval_provider import AkshareRetrievalProvider
from ._step_abstract import StepCodeGenerator, BaseStepModel
from .akshare_data_retrieval_step_model import AkShareDataRetrievalStepModel
from .llm_provider import LLMProvider
from ..planner.akshare_prompts import AksharePrompts
from ..rag.akshare_functions import AkshareFunctions
from ..planner.message import send_message
from ..akshare_doc.akshare_data_singleton import AKShareDataSingleton
from .step_data import StepData
from .llm_tools import LLMTools
from ..planner.code_enhancement_system import CodeEnhancementSystem

class AkshareDataRetrievalStepCodeGenerator(StepCodeGenerator):
    def __init__(self, step_info: AkShareDataRetrievalStepModel,step_data:StepData):
        self.step_info = step_info
        self.step_data = step_data
        self._step_code = ""
        self.llm_provider = LLMProvider()
        self.llm_client = self.llm_provider.new_llm_client()
        self.llms_cheap = self.llm_provider.new_cheap_client()
        self.akshare_docs_retrieval = AkshareRetrievalProvider()
        self.llm_tools = LLMTools()
        self.code_enhancement_system = CodeEnhancementSystem()

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

        for chunk in self.llm_client.text_chat(code_prompt, is_stream=True):
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
        for chunk in self.llm_client.text_chat(fix_prompt, is_stream=True):
            yield send_message(chunk, "code")
            fixed_code += chunk
        
        self._step_code = self._extract_code(fixed_code)
        yield send_message(f"代码已修复。")
        yield send_message(self._step_code, "code")

    def _extract_code(self, content: str) -> str:
        import re
        code_match = re.search(r'```python(.*?)```', content, re.DOTALL)
        if code_match:
            return code_match.group(1).strip()
        else:
            return content.strip()

    def make_step_sure(self):
        step_number = self.step_info.step_number
        self.step_data.set_step_code(step_number, self._step_code)

    def pre_enhancement(self) -> Generator[str, None, None]:
        enhanced_prompt = self.code_enhancement_system.apply_pre_enhancement(
            self.step_info.type,
            self.step_info.description,
            "从akshare获取数据",
        )
        self.step_info.description = enhanced_prompt
        yield send_message("代码生成提示已增强", "info")
        yield send_message(enhanced_prompt, "enhanced_prompt")

    def post_enhancement(self) -> Generator[str, None, None]:
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
        """
        
        check_result = ""
        for chunk in self.llm_client.text_chat(check_prompt, is_stream=True):
            yield send_message(chunk, "code_check")
            check_result += chunk
        
        try:
            errors = self.llm_tools.extract_json_from_text(check_result)
        except json.JSONDecodeError:
            yield send_message("无法解析检查结果，将假定代码没有错误。", "warning")
            errors = []

        # 第二步：如果有致命错误，进行修复
        if errors:
            yield send_message(f"检测到代码中存在 {len(errors)} 个潜在问题，正在进行修复...", "info")
            
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
        else:
            yield send_message("代码检查完成，未发现致命错误。", "info")

    @property
    def step_code(self) -> str:
        return self._step_code
    
    @staticmethod
    def generate_code_for_data_retrieval_prompt(
        step: AkShareDataRetrievalStepModel, 
        function_docs: Dict[str, str],
        data_summaries: List[Dict[str, str]]
    ) -> str:
        required_data = [f"{data['变量']}" for data in data_summaries]
        save_data_to = step.save_data_to
        
        return f"""
        基于以下数据检索任务：
        {step.description}

        考虑使用以下Akshare函数来完成任务：

        {json.dumps(function_docs, indent=2, ensure_ascii=False)}

        之前步骤数据变量的数据摘要：
        {json.dumps(data_summaries, indent=2, ensure_ascii=False)}

        对于之前步骤的数据，你可以使用以下变量名访问：
        {', '.join(required_data)}

        请生成一个完整的Python代码块来执行任务。遵循以下规则：

        1. 只生成一个Python代码块，使用 ```python 和 ``` 包裹。
        2. 确保代码完整可执行，并将结果保存在指定的变量中。
        3. 不要在代码块外添加任何解释或注释。
        4. 代码应考虑数据的时效性、范围、格式和结构，以及可能需要的数据预处理步骤。
        5. 如果需要多个函数配合使用，直接在代码中组合它们。
        6. 使用以下方式导入和使用akshare：
        import akshare as ak
        结果 = ak.函数名()
        7. 除非特殊说明，存储到结果变量的数据应该是函数返回的原始数据，不要进行额外的处理。
        8. 使用以下方式访问之前步骤的数据：
        from core.utils.code_tools import code_tools
        required_data = code_tools['required_data_name']
        9. 在使用之前步骤的数据时，请参考提供的数据摘要来了解数据的结构和内容。
        10. 使用以下方式保存结果：
            from core.utils.code_tools import code_tools
            
            # 对于每个需要保存的变量：
            {', '.join([f"code_tools.add('{var}', 值)" for var in save_data_to])}

        请只提供代码，不要添加任何额外的解释。代码结构示例：

        ```python
        import akshare as ak
        from core.utils.code_tools import code_tools

        # 访问之前步骤的数据（如果需要）
        {', '.join([f"{var} = code_tools['{var}']" for var in required_data])}

        # 你的代码逻辑
        # ...

        # 保存结果
        {', '.join([f"code_tools.add('{var}', 值)" for var in save_data_to])}
        ```
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