import json
from typing import Dict, Any, Generator
from core.utils.code_tools import code_tools
from core.interpreter.ast_code_runner import ASTCodeRunner
import re
from .plan_template_manager import PlanTemplateManager
from core.utils.log import logger

class StockQueryStream:
    def __init__(self, llm_client, stock_data_provider):
        self.llm_client = llm_client
        self.stock_data_provider = stock_data_provider
        self.code_runner = ASTCodeRunner()
        self.template_manager = PlanTemplateManager(llm_client)
        self.template_manager.load_templates_from_file("./json/stock_flows.md")
        code_tools.add_var('stock_data_provider', self.stock_data_provider)
        code_tools.add_var('llm_client', self.llm_client) 

    def generate_code(self, query: str) -> Generator[Dict[str, Any], None, None]:
        logger.info(f"开始生成代码: {query}")
        yield {"type": "message", "content": "开始生成代码计划..."}
        plan = yield from self._generate_plan(query)
        yield {"type": "message", "content": "计划生成完成，开始写代码..."}
        logger.info(f"执行步骤: {plan['description']}")
        yield {"type": "message", "content": f"执行步骤: {plan['description']}"}
        
        code_generator = self._generate_step_code(plan, query)
        code = ""
        prompt = ""
        for item in code_generator:
            if item["type"] == "message" and "data: [Done]" in item["content"]:
                code = item["code"]
                prompt = item["prompt"]
            yield item
        

    def query(self, query: str) -> Generator[Dict[str, Any], None, None]:
        logger.info(f"开始处理查询: {query}")
        yield {"type": "message", "content": "开始生成执行计划..."}
        plan = yield from self._generate_plan(query)
        yield {"type": "message", "content": "执行计划生成完成，开始执行..."}
        yield from self._execute_plan(plan, query)
        logger.info("查询处理完成")

    def _generate_plan(self, query: str) -> Generator[Dict[str, Any], None, None]:
        logger.info("正在生成执行计划...")
        provider_description = self.stock_data_provider.get_self_description()
        best_template = self.template_manager.get_best_template(query)
        
        # Step 1: 生成初始计划
        initial_plan_prompt = f"""
        根据以下查询要求生成一个的执行计划：
        {query}

        可用的数据提供函数如下：
        {provider_description}

        基于以下模板生成计划：
        {best_template['template']}

        请生成一个简洁的执行计划。计划应该是一个 JSON 格式的对象，包含以下字段：
        1. "description": 需要完成的任务描述
        2. "pseudocode": 完成任务的伪代码,应该是list[str]
        3. "tip_help": 关键注意事项
        4. "functions": 需要使用的数据提供函数列表

        注意：
        - 不要添加字段说明中没有说明过的字段
        - 请确保在生成计划时包含详细的提示词构建指南和输出格式要求。
        - 在伪代码的最后，请使用 code_tools.add("output_result", final_result) 来存储最终结果。
        - 对于涉及 LLM 分析，需要生成prompt的来进行分析的：
            1. 构建详细的提示词，包含所有必要的数据和上下文信息。提示词中应该阐明分析目标，分析要求。
            2. 提示词中明确指定 LLM 输出应为 JSON 格式。包含输出格式的具体要求。
            3. 使用 llm_client.one_chat(prompt) 来调用 LLM 进行分析（不使用 SSE）。

        请返回一个格式化的 JSON 计划，并用 ```json ``` 包裹。
        """

        initial_plan_response = ""
        for chunk in self.llm_client.one_chat(initial_plan_prompt, is_stream=True):
            initial_plan_response += chunk
            yield {"type": "message", "content": chunk}

        initial_plan = self._parse_plan(initial_plan_response)

        # Step 2: 使用 COT 分析计划
        cot_prompt = f"""
        请对以下执行计划进行深入思考和分析：

        {json.dumps(initial_plan, indent=2)}

        以下是计划中使用的函数的简要说明：
        {self._get_simplified_functions_docs(initial_plan['functions'])}

        请考虑以下几点：
        1. 数据获取和处理：
        - 计划中的数据获取步骤是否完整？是否遗漏了重要数据？
        - 数据处理逻辑是否高效和合理？
        - 函数的使用是否正确？参数和返回值是否符合函数文档的描述？

        2. 提示词构建：
        - 计划中的LLM提示词是否足够详细和明确？
        - 提示词中是否包含足够明确的输出要求。
        - 提示词中是否包阐明分析目标，分析要求。
        - 如何改进提示词以确保获得高质量的分析结果？

        3. 伪代码中是否包含错误：
        - 伪代码是否错误访问了数据，比如对str使用了['indicator'],是否对str使用了get
        - 函数调用是否符合函数文档的描述？
        - 如何增强计划的鲁棒性？

        4. 伪代码的逻辑错误：
        - 当对数个值的结果进行评分，这些值是否在同一个数值段？
        - 是否访问了错误的数据

        请提供您的分析和改进建议，但不要直接修改计划。特别注意检查函数使用是否符合提供的函数文档。
        """

        cot_response = ""
        for chunk in self.llm_client.one_chat(cot_prompt, is_stream=True):
            cot_response += chunk
            yield {"type": "message", "content": chunk}

        # Step 3: 使用 Self-reflection 优化计划
        reflection_prompt = f"""
        基于之前的分析，请对以下执行计划进行优化：

        原始计划：
        {json.dumps(initial_plan, indent=2)}

        分析和建议：
        {cot_response}

        请根据分析结果优化计划，重点关注：
        1. 提高提示词的质量和明确性
        2. 确保数据处理步骤的完整性和效率
        3. 伪代码中的逻辑错误

        同时，请确保优化后的计划仍然简洁明了，不要过度复杂化。

        请返回优化后的计划，使用 JSON 格式并用 ```json ``` 包裹。
        """

        optimized_response = ""
        for chunk in self.llm_client.one_chat(reflection_prompt, is_stream=True):
            optimized_response += chunk
            yield {"type": "message", "content": chunk}

        optimized_plan = self._parse_plan(optimized_response)

        logger.info("执行计划生成完成")
        yield {"type": "message", "content": "data: [Done]", "plan": optimized_plan}
        return optimized_plan
    
    def _get_simplified_functions_docs(self, function_names: list) -> str:
        docs = []
        for func_name in function_names:
            full_doc = self.stock_data_provider.get_function_docstring(func_name)
            # Extract the first sentence or line as a simplified description
            simplified_doc = full_doc.split('.')[0] + '.'
            docs.append(f"{func_name}: {simplified_doc}")
        return "\n".join(docs)
    
    def _parse_plan(self, plan_response: str) -> dict:
        json_pattern = r'```json\s*(.*?)\s*```'
        matches = re.findall(json_pattern, plan_response, re.DOTALL)
        if matches:
            return json.loads(matches[0])
        else:
            raise ValueError("无法解析计划 JSON")

    def _get_functions_docs(self, function_names: list) -> str:
        docs = []
        for func_name in function_names:
            doc = self.stock_data_provider.get_function_docstring(func_name)
            docs.append(f"{func_name}:\n{doc}\n")
        return "\n".join(docs)

    def _extract_code(self, response: str) -> str:
        code_pattern = r'```python\s*(.*?)\s*```'
        matches = re.findall(code_pattern, response, re.DOTALL)
        return matches[0] if matches else response

    def _execute_plan(self, plan: dict, query: str) -> Generator[Dict[str, Any], None, None]:
        logger.info(f"执行步骤: {plan['description']}")
        yield {"type": "message", "content": f"执行步骤: {plan['description']}"}
        
        code_generator = self._generate_step_code(plan, query)
        code = ""
        prompt = ""
        for item in code_generator:
            if item["type"] == "message" and "data: [Done]" in item["content"]:
                code = item["code"]
                prompt = item["prompt"]
            yield item

        yield from self._execute_code(code, prompt)

    def _generate_step_code(self, step: dict, query: str) -> Generator[Dict[str, Any], None, None]:
        logger.info("正在生成步骤代码...")
        yield {"type": "message", "content": "正在生成步骤代码..."}
        functions_docs = self._get_functions_docs(step['functions'])

        prompt = f"""
        根据以下步骤信息和函数文档，生成可执行的Python代码：

        总查询需求: {query}
        步骤描述：{step['description']}
        伪代码：{step['pseudocode']}
        注意事项: {step["tip_help"]}

        stock_data_provider可用函数文档：
        {functions_docs}

        请生成完整的、可执行的Python代码来完成这个步骤。确保代码可以直接运行，并遵循以下规则：
        1. 在代码开头添加：
        ```python
        from core.utils.code_tools import code_tools
        stock_data_provider = code_tools["stock_data_provider"]
        llm_client = code_tools["llm_client"]
        ```
        2. 使用 stock_data_provider 来调用数据提供函数
        3. 使用 llm_client.one_chat(prompt) 来调用 LLM 进行分析
        4. 仅使用"stock_data_provider可用函数文档"中提供的函数来获取数据
        5. 仔细检查函数文档，确保正确的调用了函数，确保正确的使用了函数结果。因为伪代码阶段产生的函数调用和返回值使用可能是错误的。
        6. 确保在代码的最后使用 code_tools.add("output_result", final_result) 来存储最终结果

        对于涉及 LLM 分析的部分，即便伪代码没有提及，也需要确保：
        1. 构建详细的提示词，包含所有必要的数据和上下文信息。
        2. 明确指定 LLM 输出应为 JSON 格式。
        3. 在提示词中包含具体的评分标准、推荐理由长度限制和风险因素识别要求。
        4. 提示词中包含了"模板"中所要求的内容。

        请只提供 Python 代码，不需要其他解释。
        """

        code_response = ""
        for chunk in self.llm_client.one_chat(prompt, is_stream=True):
            code_response += chunk
            yield {"type": "message", "content": chunk}

        logger.info("步骤代码生成完成")
        yield {"type": "message", "content": "步骤代码生成完成"}
        extracted_code = self._extract_code(code_response)
        yield {"type": "code", "content": extracted_code}
        yield {"type": "message", "content": "data: [Done]", "code": extracted_code, "prompt": prompt}

    def _execute_code(self, code: str, prompt: str, max_attempts: int = 8) -> Generator[Dict[str, Any], None, None]:
        logger.info("正在执行代码...")
        attempt = 1
        while attempt <= max_attempts:
            try:
                yield {"type": "message", "content": f"执行代码（尝试 {attempt}/{max_attempts}）..."}
                result = self.code_runner.run(code)
                if result['error']:
                    if attempt < max_attempts:
                        logger.warning(f"代码执行出错（尝试 {attempt}/{max_attempts}），正在修复...")
                        yield {"type": "message", "content": f"代码执行出错，正在修复...（尝试 {attempt}/{max_attempts}）"}
                        yield {"type": "message", "content": f"{result['error']}"}
                        fix_generator = self._fix_runtime_error(code, result['error'], prompt)
                        for item in fix_generator:
                            if item["type"] == "message" and "data: [Done]" in item["content"]:
                                code = item["code"]
                            yield item
                        attempt += 1
                    else:
                        logger.error(f"代码执行失败，已达到最大尝试次数 ({max_attempts})。最后一次错误: {result['error']}")
                        yield {"type": "message", "content": f"代码执行失败，错误: {result['error']}"}
                        return
                else:
                    logger.info(f"代码执行成功（尝试 {attempt}/{max_attempts}）")
                    yield {"type": "message", "content": "代码执行成功，正在生成结果..."}
                    if 'output_result' in code_tools:
                        result = code_tools['output_result']
                        yield from self._format_result(result)
                    else:
                        yield {"type": "message", "content": "未能获取查询结果"}
                    return
            except Exception as e:
                if attempt < max_attempts:
                    logger.warning(f"执行代码时发生异常（尝试 {attempt}/{max_attempts}）: {str(e)}，正在尝试修复...")
                    yield {"type": "message", "content": f"执行代码时发生异常，正在修复...（尝试 {attempt}/{max_attempts}）"}
                    fix_generator = self._fix_runtime_error(code, str(e), prompt)
                    for item in fix_generator:
                        if item["type"] == "message" and "data: [Done]" in item["content"]:
                            code = item["code"]
                        yield item
                    attempt += 1
                else:
                    logger.error(f"代码执行失败，已达到最大尝试次数 ({max_attempts})。最后一次错误: {str(e)}")
                    yield {"type": "message", "content": f"代码执行失败，错误: {str(e)}"}
                    return

        logger.error(f"代码执行失败，已达到最大尝试次数 ({max_attempts})。")
        yield {"type": "message", "content": "代码执行失败，请稍后重试。"}

    def _fix_runtime_error(self, code: str, error: str, prompt: str) -> Generator[Dict[str, Any], None, None]:
        logger.info("正在修复运行时错误...")
        yield {"type": "message", "content": "正在修复运行时错误..."}
        fix_prompt = f"""
        执行以下代码时发生了错误：

        {code}

        错误信息：
        {error}

        原始提示词：
        {prompt}

        请修正代码以解决这个错误。请只提供修正后的完整代码，不需要其他解释。
        确保代码遵循原始提示词中的所有要求和规则，特别是：
        1. 使用 llm_client.one_chat(prompt) 来调用 LLM 进行分析（不使用 SSE）
        2. 对于 LLM 分析步骤，确保提示词详细且符合要求
        3. 使用 code_tools.add("output_result", final_result) 来存储最终结果
        """
        fixed_code_response = ""
        for chunk in self.llm_client.one_chat(fix_prompt, is_stream=True):
            fixed_code_response += chunk
            yield {"type": "message", "content": chunk}

        logger.info("错误修复代码生成完成")
        yield {"type": "message", "content": "错误修复代码生成完成"}
        fixed_code = self._extract_code(fixed_code_response)
        yield {"type": "code", "content": fixed_code}
        yield {"type": "message", "content": "data: [Done]", "code": fixed_code}

    def _format_result(self, result: str) -> Generator[Dict[str, Any], None, None]:
        markdown_prompt = f"""
        请将以下查询结果转换为清晰、结构化的Markdown格式：

        结果:
        {result}

        请确保:
        1. 使用适当的Markdown标记（如标题、列表、表格等）来组织信息。
        2. 保留所有重要信息，但以更易读的方式呈现。
        3. 如果结果中包含数字数据，考虑使用表格形式展示。
        4. 为主要部分添加简短的解释或总结。
        5. 如果有多个部分，使用适当的分隔和标题。

        请直接返回Markdown格式的文本，无需其他解释。
        """
        
        yield {"type": "message", "content": "正在格式化结果..."}
        
        markdown_result = ""
        for chunk in self.llm_client.one_chat(markdown_prompt, is_stream=True):
            markdown_result += chunk
            yield {"type": "message", "content": chunk}
        
        yield {"type": "message", "content": "结果格式化完成"}
        yield {"type": "message", "content": markdown_result}

    def optimize_code(self, code: str, prompt: str) -> Generator[Dict[str, Any], None, None]:
        logger.info("开始优化代码...")
        yield {"type": "message", "content": "开始优化代码..."}

        # Step 1: COT 分析
        cot_prompt = f"""
        请对以下代码进行深入思考和分析：

        {code}

        原始提示词：
        {prompt}

        请考虑以下几点：
        1. 代码逻辑：
        - 代码是否完全实现了原始提示词中的要求？
        - 代码逻辑是否清晰、高效？
        - 是否有冗余或可以优化的部分？

        2. 致命错误
        - 代码中是否存在影响运行的致命错误？
        - 是否存在错误的类型处理？

        3. 数据处理：
        - 数据的获取和处理是否正确？
        - 是否有更高效的数据处理方式？

        4. LLM 提示词构建：
        - LLM 的提示词是否足够清晰和具体？
        - 提示词要求的输出格式是否足够明确？
        - 是否需要改进提示词以获得更好的结果？

        注意:
        - 不要检查llm_client.one_chat的可用性，这是一个可以访问的函数
        
        请提供您的分析和改进建议，但不要直接修改代码。
        """

        cot_response = ""
        for chunk in self.llm_client.one_chat(cot_prompt, is_stream=True):
            cot_response += chunk
            yield {"type": "message", "content": chunk}

        # Step 2: Self-reflection 和代码优化
        reflection_prompt = f"""
        基于之前的分析，请优化以下代码：

        原始代码：
        {code}

        分析和建议：
        {cot_response}

        原始提示词：
        {prompt}

        请根据分析结果优化代码，重点关注：
        1. 提高代码的效率和可读性
        2. 修正致命错误
        3. 改进数据处理逻辑
        4. 优化 LLM 提示词
        5. 确保代码完全符合原始提示词的要求

        请返回优化后的完整代码，使用 Python 格式并用 ```python ``` 包裹。
        同时，请简要说明您做出的主要更改和优化。
        """

        optimized_response = ""
        for chunk in self.llm_client.one_chat(reflection_prompt, is_stream=True):
            optimized_response += chunk
            yield {"type": "message", "content": chunk}

        # 提取优化后的代码
        optimized_code = self._extract_code(optimized_response)

        logger.info("代码优化完成")
        yield {"type": "message", "content": "代码优化完成"}
        yield {"type": "code", "content": optimized_code}
        yield {"type": "message", "content": "data: [Done]", "code": optimized_code}