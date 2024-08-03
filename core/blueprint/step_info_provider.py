from ._step_abstract import StepInfoGenerator
from .current_generator_collection import CurrentGeneratorCollection



class StepInfoProvider:
    def __init__(self):
        self.generators = CurrentGeneratorCollection()
    
    def select_generator(self, step_type:str)->StepInfoGenerator:
        return self.generators[step_type]

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
   - "task"：描述该步骤需要完成的具体任务,任务描述应该尽可能具体，避免模糊或不清晰的描述。
   - "save_data_to":一个数组,可以是空数组，包含这个步骤产生的数据的描述性变量名。变量名用英文。必须是后续步骤需要使用的变量，如果后续步骤不需要就不用写。如果需要保存多个值，需要在task里面详细说明每个值是什么数据。
   - "required_data"：一个数组，可以是空数组，包含这个步骤需要的数据，必须是之前步骤中 save_data_to 里面的变量名。
7. 确保你的计划是逻辑合理的，步骤之间有明确的关联和顺序。任务描述情绪具体。
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
    

    def get_fix_prompt(self, query: str, last_steps: dict, generate_error: str) -> str:
        generator_list = []
        for k, v in self.generators.items():
            generator_list.append({"step": k, "description": v.step_description})
        
        prompt = f"""
    你是一个严格遵循指令的 AI 助手。你的任务是基于给定的查询、上一次生成的步骤和发生的错误，修复并改进计划。

    用户查询："{query}"

    上次生成的步骤：
    {last_steps}

    生成时发生的错误：
    {generate_error}

    generator_list:
    {generator_list}

    请仔细阅读以下说明，并确保你的回答完全符合要求：

    1. 分析上次生成的步骤和发生的错误，找出问题所在。
    2. 基于用户的查询、可用的步骤类型和错误信息，修改并改进计划。
    3. 每个步骤都应该对应 generator_list 中的一个步骤类型。
    4. 你的修改后的计划应该解决之前的错误，并更好地实现用户查询的目标。
    5. 生成的计划必须是一个 JSON 数组，并用 ``` 符号包裹。
    6. 数组中的每个元素都是一个对象，包含以下字段：
        - "step_type"：必须与 generator_list 中的 "step" 值完全匹配
        - "task"：描述该步骤需要完成的具体任务,任务描述应该尽可能具体，避免模糊或不清晰的描述。
        - "save_data_to":一个数组,可以是空数组，包含这个步骤产生的数据的描述性变量名。变量名用英文。必须是后续步骤需要使用的变量，如果后续步骤不需要就不用写。如果需要保存多个值，需要在task里面详细说明每个值是什么数据。
        - "required_data"：一个数组，可以是空数组，包含这个步骤需要的数据，必须是之前步骤中 save_data_to 里面的变量名。
    7. 确保你的修改后的计划是逻辑合理的，步骤之间有明确的关联和顺序。
    8. 不要在你的回答中包含任何对 generator_list 具体内容的直接引用或假设。
    9. 你的回答必须且只能是一个 JSON 数组，不要包含任何额外的结构或字段。
    10. 不要在 JSON 数组外添加任何说明、注释或额外的文本。
    11. 如果某个步骤不需要保存数据或不需要之前的数据，相应的字段应为空数组。
    12. 特别注意解决 generate_error 中提到的问题，并在相关步骤中做出必要的调整。

    示例格式（注意：这只是格式示例，你的实际内容应该基于用户查询和错误信息）：
    ```json
    [
    {{"step_type": "example_step", "task": "修改后的任务内容", "save_data_to": ["example_data"], "required_data": []}},
    {{"step_type": "another_step", "task": "修改后的任务内容", "save_data_to": [], "required_data": ["example_data"]}}
    ]
    ```

    请严格按照以上说明和示例格式，为用户查询生成一个修正后的、详细的、结构化的计划。确保你的回答仅包含所要求的 JSON 数组，不要添加任何额外的解释、评论或结构。
    """
        return prompt

    def get_modify_prompt(self, query: str, last_steps: dict) -> str:
        generator_list = []
        for k, v in self.generators.items():
            generator_list.append({"step": k, "description": v.step_description})
        
        prompt = f"""
    你是一个严格遵循指令的 AI 助手。你的任务是基于给定的查询和之前生成的步骤，修改并改进计划。

    用户查询："{query}"

    之前生成的步骤：
    {last_steps}

    generator_list:
    {generator_list}

    请仔细阅读以下说明，并确保你的回答完全符合要求：

    1. 分析之前生成的步骤和用户的新查询，找出需要修改的地方。
    2. 基于用户的新查询和可用的步骤类型，修改并改进计划。
    3. 每个步骤都应该对应 generator_list 中的一个步骤类型。
    4. 你的修改后的计划应该更好地实现用户新查询的目标。
    5. 生成的计划必须是一个 JSON 数组，并用 ``` 符号包裹。
    6. 数组中的每个元素都是一个对象，包含以下字段：
    - "step_type"：必须与 generator_list 中的 "step" 值完全匹配
    - "task"：描述该步骤需要完成的具体任务
    - "save_data_to"：一个数组，包含这个步骤产生的数据的描述性变量名。变量名用英文。后续步骤需要使用。
    - "required_data"：一个数组，包含这个步骤需要的数据，必须是之前步骤中的 save_data_to 变量名。
    7. 确保你的修改后的计划是逻辑合理的，步骤之间有明确的关联和顺序。
    8. 不要在你的回答中包含任何对 generator_list 具体内容的直接引用或假设。
    9. 你的回答必须且只能是一个 JSON 数组，不要包含任何额外的结构或字段。
    10. 不要在 JSON 数组外添加任何说明、注释或额外的文本。
    11. 如果某个步骤不需要保存数据或不需要之前的数据，相应的字段应为空数组。
    12. 你可以添加新的步骤、删除不必要的步骤、修改现有步骤的内容，或者重新排序步骤，以更好地满足新的查询要求。

    示例格式（注意：这只是格式示例，你的实际内容应该基于用户新查询）：
    ```json
    [
    {{"step_type": "example_step", "task": "修改后的任务内容", "save_data_to": ["example_data"], "required_data": []}},
    {{"step_type": "another_step", "task": "修改后的任务内容", "save_data_to": [], "required_data": ["example_data"]}}
    ]
    ```
    请严格按照以上说明和示例格式，为用户的新查询生成一个修改后的、详细的、结构化的计划。确保你的回答仅包含所要求的 JSON 数组，不要添加任何额外的解释、评论或结构。
    """
        return prompt