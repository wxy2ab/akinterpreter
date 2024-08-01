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
            return

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

    def pre_enhancement(self) -> Generator[str, None, None]:
        pass

    def post_enhancement(self) -> Generator[str, None, None]:
        pass

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