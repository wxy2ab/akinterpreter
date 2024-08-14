




import json
from typing import Any, Dict, Generator
from tenacity import retry, retry_if_exception, stop_after_attempt
from core.blueprint._step_abstract import StepCodeGenerator
from core.blueprint.llm_parse.step_model import LLMParseStepModel
from core.blueprint.llm_provider import LLMProvider
from core.blueprint.llm_tools import LLMTools
from core.blueprint.step_data import StepData
from core.planner.code_enhancement_system import CodeEnhancementSystem
from core.planner.message import send_message
from core.utils.code_tools import code_tools


class LLMParseStepCodeGenerator(StepCodeGenerator):
    def __init__(self,step_info: LLMParseStepModel,step_data:StepData):
        self.step_info = step_info
        self.step_data = step_data
        self._step_code = ""
        self.llm_provider = LLMProvider()
        self.llm_tools = LLMTools()
        self.code_enhancement_system = CodeEnhancementSystem()
        self.llm_client = self.llm_provider.new_llm_client()
        self.llms_cheap = self.llm_provider.new_cheap_client()

    def make_step_sure(self):
        step_number = self.step_info.step_number
        self.step_data.set_step_code(step_number, self._step_code)
        
    @property
    def step_code(self) -> str:
        return self._step_code


    @retry(stop=stop_after_attempt(3), retry=retry_if_exception(False))
    def gen_step_code(self) -> Generator[Dict[str, Any], None, None]:
        description = self.step_info.description
        required_data_list = self.step_info.required_data
        save_data_to = self.step_info.save_data_to

        data_summaries = []
        has_callable = False

        for data_var in required_data_list:
            real_var = code_tools[data_var]
            if callable(real_var):
                has_callable = True
            data_summary = self.step_data.get(f"{data_var}_summary", "数据摘要不可用")
            data_summaries.append({"变量": data_var, "摘要": data_summary})

        if not has_callable:
            # 情况1：没有可调用函数，直接生成代码
            yield from self._generate_code_without_callable(description, data_summaries, save_data_to)
        else:
            # 情况2：有可调用函数，生成包含调用代码的完整代码
            yield from self._generate_code_with_callable(description, data_summaries, save_data_to)

    def _generate_code_without_callable(self, description, data_summaries, save_data_to):
        code_prompt = f"""
        请根据以下信息生成Python代码:
        
        任务描述: {description}
        数据摘要:
        {json.dumps(data_summaries, ensure_ascii=False, indent=2)}
        需要保存的变量: {', '.join(save_data_to)}
        
        请生成一个完整的Python代码块，包括以下内容：
        1. 从code_tools中获取所需的数据
        2. 创建一个主函数，实现所需的功能
        3. 为主函数编写详细的docstring，描述函数功能、参数和返回值
        4. 编写简单的测试代码，验证主函数的正确性
        5. 使用 code_tools.add() 方法保存主函数到指定的变量: {', '.join(save_data_to)}
        
        确保生成的代码是完整的、可以直接运行的，并包含所有必要的步骤。
        不需要在代码中打印中间结果或数据摘要，专注于实现所需的功能和保存结果。
        """

        generated_code = ""
        for chunk in self.llm_client.one_chat(code_prompt, is_stream=True):
            yield send_message(chunk, "code")
            generated_code += chunk

        self._step_code = generated_code
        yield send_message("代码生成成功。", "success")

    def _generate_code_with_callable(self, description, data_summaries, save_data_to):
        code_prompt = f"""
        请根据以下信息生成Python代码:
        
        任务描述: {description}
        数据摘要:
        {json.dumps(data_summaries, ensure_ascii=False, indent=2)}
        需要保存的变量: {', '.join(save_data_to)}

        生成代码完成以下步骤：
        1. 从code_tools中获取所需的数据和函数
        2. 执行可调用函数，获得结果
        3. 使用 data_summarizer = code_tools["data_summarizer"] 获取数据摘要器
        4. 对函数调用的结果生成数据摘要：data_summary = data_summarizer.get_data_summary(data) 生成数据摘要
        5. 使用 llm_client = code_tools["llm_client"] 获取LLM客户端
        6. 使用以下提示词调用 llm_client.one_chat() 生成最终代码：

        ```
        请根据以下信息生成Python代码:
        
        任务描述: {description}
        数据摘要:
        {{updated_data_summaries}}
        需要保存的变量: {', '.join(save_data_to)}
        
        请生成一个完整的Python代码块，包括以下内容：
        1. 从code_tools中获取所需的数据
        2. 创建一个主函数，实现所需的功能
        3. 为主函数编写详细的docstring，描述函数功能、参数和返回值
        4. 编写简单的测试代码，验证主函数的正确性
        5. 使用 code_tools.add() 方法保存主函数到指定的变量: {', '.join(save_data_to)}
        
        确保生成的代码是完整的、可以直接运行的，并包含所有必要的步骤。
        不需要在代码中打印中间结果或数据摘要，专注于实现所需的功能和保存结果。
        ```

        7. 使用 llm_tools = code_tools["llm_tools"] 获取 LLM 工具
           然后使用 extracted_code = llm_tools.extract_code(generated_content) 从生成的内容中提取代码
        8. 使用 code_runner = code_tools["code_runner"] 获取代码运行器
           然后使用 result = code_runner.run(extracted_code) 执行提取的代码
           检查 result 字典中的 'error' 键，如果存在错误，请处理它

        确保生成的代码是完整的、可以直接运行的，并包含所有必要的步骤。
        最终生成的代码应该包含主函数的实现、测试和保存步骤，就像在无可调用函数的情况下一样。
        """

        generated_code = ""
        for chunk in self.llm_client.one_chat(code_prompt, is_stream=True):
            yield send_message(chunk, "code")
            generated_code += chunk

        self._step_code = generated_code
        yield send_message("代码生成成功。", "success")