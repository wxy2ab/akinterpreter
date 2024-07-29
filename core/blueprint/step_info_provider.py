from .current_generator_collection import CurrentGeneratorCollection



class StepInfoProvider:
    def __init__(self):
        self.generators = CurrentGeneratorCollection()
    
    def get_build_prompt(self, query: str) -> str:
        generator_list = []
        for k,v in self.generators.items():
            generator_list.append({"step":k,"description":v.step_description})   
        prompt=f"""
你是一个严格遵循指令的 AI 助手。你的任务是基于给定的查询和可用的步骤类型创建一个详细的计划。

用户查询："{query}"

generator_list:
{generator_list}

请仔细阅读以下说明，并确保你的回答完全符合要求：

1. 你将获得一个 generator_list，其中包含可用的步骤类型及其描述。
2. 基于用户的查询和可用的步骤类型，创建一个多步骤计划。
3. 每个步骤都应该对应 generator_list 中的一个步骤类型。
4. 你的计划应该通过实现这些步骤的内容，最终实现用户查询的目标。
5. 生成的计划必须是一个 JSON 数组，并用 ``` 符号包裹。
6. 数组中的每个元素都是一个对象，包含以下字段：
   - "step_type"：必须与 generator_list 中的 "step" 值完全匹配
   - "task"：描述该步骤需要完成的具体任务
   - "save_data_to"：一个数组，包含这个步骤产生的数据的描述性变量名
   - "required_data"：一个数组，包含这个步骤需要的数据，使用之前步骤中的 save_data_to 变量名
7. 确保你的计划是逻辑合理的，步骤之间有明确的关联和顺序。
8. 不要在你的回答中包含任何对 generator_list 具体内容的直接引用或假设。
9. 你的回答必须且只能是一个 JSON 数组，不要包含任何额外的结构或字段。
10. 不要在 JSON 数组外添加任何说明、注释或额外的文本。
11. 如果某个步骤不需要保存数据或不需要之前的数据，相应的字段应为空数组。

示例格式（注意：这只是格式示例，你的实际内容应该基于用户查询）：
```json
[
{{"step_type": "example_step", "task": "任务内容", "save_data_to": ["example_data"], "required_data": []}},
{{"step_type": "another_step", "task": "任务内容", "save_data_to": [], "required_data": ["example_data"]}}
]
```

请严格按照以上说明和示例格式，为用户查询生成一个详细的、结构化的计划。确保你的回答仅包含所要求的 JSON 数组，不要添加任何额外的解释、评论或结构。
"""
        return prompt
    
    