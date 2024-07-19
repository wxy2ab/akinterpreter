import json
from typing import Any, Dict, List


class AksharePrompts:
    @staticmethod
    def create_plan_prompt(query: str, categories: Dict[str, str]) -> str:
        category_descriptions = "\n".join([f"- {cat}: {desc}" for cat, desc in categories.items()])
        category_list = ", ".join([f'"{cat}"' for cat in categories.keys()])
        
        return f"""
        你是一个严格遵循指令的 AI 助手。你的任务是基于给定的查询创建一个数据检索和分析计划。
        请仔细阅读以下说明，并确保你的回答完全符合要求。

        基于用户查询："{query}"

        创建一个数据检索和分析计划。

        检索计划中，data_category的值应该从以下列表中选择：{category_list}。
        下面是检索计划之中可用的data_category数据类别及其详细说明：

        {category_descriptions}


        创建一个详细的计划来检索和分析数据。请注意以下要点：
        1. 不同类型的数据可能需要通过不同的步骤分别获取。
        2. 每个数据检索步骤应该专注于获取一种特定类型的数据。
        3. 在所有必要的数据都获取之后，再进行数据分析步骤。
        4. 仔细匹配数据需求与类别说明，确保选择最合适的data_category。
        例如：
        - 如需财务数据，应选择"股票数据"类别。
        - 如需基本面数据，应选择"公司数据"类别（包含公司概况、财务报表等）。

        该计划应采用JSON格式，具有以下结构：
        {{
            "query_summary": "查询的总结和提炼",
            "steps": [
                {{
                    "step_number": 1,
                    "description": "步骤描述，详细而明确",
                    "type": "data_retrieval",
                    "data_category": "必须从给定类别中精确选择",
                    "save_data_to": "描述性的变量名，如 stock_financial_data"
                }},
                // 可能有多个数据检索步骤
                {{
                    "step_number": 2,
                    "description": "步骤描述，详细而明确",
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
        5. 变量名应该是描述性的，易于理解的，如 stock_financial_data, company_fundamental_data 等。
        6. 计划包括所有必要的数据检索步骤，以及后续的数据分析步骤。
        7. 保持计划尽量简单，如无必要，不新增步骤。

        请提供完整的JSON格式计划，确保其可以被直接解析为Python字典。
        """

    @staticmethod
    def fix_plan_prompt(plan: Dict[str, Any], error_message: str, categories: Dict[str, str]) -> str:
        return f"""
        以下是一个需要修复的计划：
        {json.dumps(plan, indent=2, ensure_ascii=False)}

        修复这个计划中的以下错误：
        {error_message}

        可用的数据类别有：
        {json.dumps(categories, indent=2, ensure_ascii=False)}

        请参考以下示例，提供修复后的完整计划：

        示例查询: "分析阿里巴巴的财务状况和市场表现"
        示例计划:
        {{
            "query_summary": "分析阿里巴巴的财务状况和市场表现",
            "steps": [
                {{
                    "step_number": 1,
                    "description": "获取阿里巴巴的财务数据",
                    "type": "data_retrieval",
                    "data_category": "股票数据",
                    "save_data_to": "alibaba_financial_data"
                }},
                {{
                    "step_number": 2,
                    "description": "获取阿里巴巴的业绩报告数据",
                    "type": "data_retrieval",
                    "data_category": "公司数据",
                    "save_data_to": "alibaba_report_data"
                }},
                {{
                    "step_number": 3,
                    "description": "分析阿里巴巴的财务状况和市场表现",
                    "type": "data_analysis",
                    "required_data": ["alibaba_financial_data", "alibaba_report_data"]
                }}
            ]
        }}

        上面的例子中，query要求找市场数据，但是没有这个类别，所从公司数据中选择了业绩报告

        请确保修复后的计划：
        1. 包含完整的查询总结（query_summary）。
        2. 包含所有必要的步骤，每个步骤都有正确的步骤编号（step_number）。
        3. 数据检索步骤（data_retrieval）必须包含有效的数据类别（data_category）和保存数据的变量名（save_data_to）。
        4. 数据分析步骤（data_analysis）必须包含所需数据的列表（required_data）。
        5. 所有步骤都有清晰、详细的描述（description）。
        6. 如果没有完全匹配的数据类别，选择最接近的类别。

        请提供修复后的完整计划，确保其符合所有要求并可以被直接解析为Python字典。
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
        6. 目前步骤的类型只支持 "data_retrieval" 和 "data_analysis"。其他类型均会不允许。

        请提供修改后的完整JSON格式计划，确保其可以被直接解析为Python字典。
        如果json内容和plain text混合输出，确保json内容用```json和```包裹。
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
        7. 除非特殊说明，存储到结果变量的数据应该是函数返回的原始数据，不要进行额外的处理。

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
    def select_functions_from_category_prompt(step: Dict[str, Any], functions: List[str],descriptions:str) -> str:
        return f"""
        基于以下数据检索任务：
        {step['description']}

        从以下函数中选择1到5个最合适的函数：
        {json.dumps(functions, indent=2, ensure_ascii=False)}

        函数说明：
        {descriptions}

        请返回选中的函数名称列表，用逗号分隔。不需要其他解释。
        """

    @staticmethod
    def generate_data_analysis_code_prompt(step: Dict[str, Any], data_summaries: Dict[str, str], allow_yfinance: bool) -> str:
        save_data_instruction = ""
        if 'save_data_to' in step:
            save_data_instruction = f"""
        9. 除了分析结果外，请将原始数据（非分析结果）存储在变量 '{step['save_data_to']}' 中。
           这个变量应该包含用于分析的原始数据，而不是分析后的结果。
        """

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
        {save_data_instruction}

        如果需要使用LLM API进行分析，请使用以下代码获取一个新的LLMApiClient实例：

        llm_client = llm_factory.get_instance()
        response = llm_client.one_chat("你的提示词")  # 单次分析任务用one_chat(str)方法, 多次分析任务用换成text_chat(str)方法

        可用的变量和对象：
        - llm_factory: LLMFactory 实例，用于获取新的 LLMApiClient
        - code_runner: CodeRunner 实例
        - data_summarizer: DataSummarizer 实例,用于获得数据摘要
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
        # 例如：data = {step['required_data'][0] if step['required_data'] else 'your_data_variable'}

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

        {f"# 保存原始数据到 {step['save_data_to']} 变量" if 'save_data_to' in step else ''}
        {f"{step['save_data_to']} = data  # 假设 'data' 是您的原始数据变量" if 'save_data_to' in step else ''}
        ```

        请确保代码完整可执行，并将分析结果保存在名为'analysis_result'的变量中。
        {f"同时，请将原始数据保存在名为'{step['save_data_to']}'的变量中。" if 'save_data_to' in step else ''}
        """

    @staticmethod
    def generate_enhanced_code_for_data_retrieval_prompt(
        step: Dict[str, Any], 
        function_docs: Dict[str, str],
        data_summaries: Dict[str, str]
    ) -> str:
        required_data = step.get('required_data', [])
        
        return f"""
        基于以下数据检索任务：
        {step['description']}

        考虑使用以下Akshare函数来完成任务：

        {json.dumps(function_docs, indent=2, ensure_ascii=False)}

        之前步骤数据变量的数据摘要：
        {json.dumps(data_summaries, indent=2, ensure_ascii=False)}

        对于之前步骤的数据，你可以使用以下变量名访问：
        {', '.join(required_data)}

        请生成一个完整的Python代码块来执行任务。遵循以下规则：

        1. 只生成一个Python代码块，使用 ```python 和 ``` 包裹。
        2. 确保代码完整可执行，并将结果保存在一个名为'{step['save_data_to']}'的变量中。
        3. 不要在代码块外添加任何解释或注释。
        4. 代码应考虑数据的时效性、范围、格式和结构，以及可能需要的数据预处理步骤。
        5. 如果需要多个函数配合使用，直接在代码中组合它们。
        6. 确保最终结果被赋值给变量 '{step['save_data_to']}'，而不是其他名称。
        7. 除非特殊说明，存储到结果变量的数据应该是函数返回的原始数据，不要进行额外的处理。
        8. 如果需要使用之前步骤的数据，请直接使用相应的变量名。
        9. 在使用之前步骤的数据时，请参考提供的数据摘要来了解数据的结构和内容。

        请只提供代码，不要添加任何额外的解释。
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

    @staticmethod
    def schedule_run_prompt(schedule_query: str, current_time: str) -> str:
        return f"""
        基于以下调度请求和当前时间，请提供适当的调度参数：

        调度请求: {schedule_query}
        当前时间: {current_time}

        请提供以下格式的 JSON 响应：
        {{
            "trigger": "date" 或 "interval" 或 "cron",
            "trigger_args": {{
                // 相应的触发器参数
            }}
        }}

        对于 "date" 触发器，请使用 "run_date" 参数。
        对于 "interval" 触发器，可以使用 "weeks", "days", "hours", "minutes", "seconds" 等参数。
        对于 "cron" 触发器，可以使用 "year", "month", "day", "week", "day_of_week", "hour", "minute", "second" 等参数。

        如果无法解析请求，请返回 {{"error": "无法解析调度请求"}}。
        """

    @staticmethod
    def modify_step_code_prompt(current_code: str, query: str) -> str:
        return f"""
        当前代码：
        {current_code}

        修改请求：
        {query}

        请根据修改请求提供更新后的完整代码。只返回修改后的代码，不需要任何解释。
        代码用 ```python 和 ``` 包裹。
        """

    @staticmethod
    def schedule_run_prompt(schedule_query: str, current_time: str) -> str:
        return f"""
        基于以下调度请求和当前时间，请提供适当的调度参数：

        调度请求: {schedule_query}
        当前时间: {current_time}

        请提供以下格式的 JSON 响应：
        {{
            "trigger": "date" 或 "interval" 或 "cron",
            "trigger_args": {{
                // 相应的触发器参数
            }}
        }}

        对于 "date" 触发器，请使用 "run_date" 参数。
        对于 "interval" 触发器，可以使用 "weeks", "days", "hours", "minutes", "seconds" 等参数。
        对于 "cron" 触发器，可以使用 "year", "month", "day", "week", "day_of_week", "hour", "minute", "second" 等参数。

        如果无法解析请求，请返回 {{"error": "无法解析调度请求"}}。
        """
    
    @staticmethod
    def fix_code_prompt_review(self, code: str, error: str, review_results: str) -> str:
        return f"""
        原始代码：
        {code}

        遇到的错误：
        {error}

        代码审查结果：
        {review_results}

        请根据以上信息修复代码。提供完整的修复后的代码。
        """