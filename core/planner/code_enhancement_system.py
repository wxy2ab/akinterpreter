import json
import os
from typing import Dict, Any, Generator, List, Callable
from core.llms.llm_factory import LLMFactory

class CodeEnhancementSystem:
    def __init__(self):
        self.llm_client = LLMFactory().get_instance()
        self.pre_enhancement_rules = self._load_json_rules("./json/pre_code_enhancement.json")
        self.post_enhancement_rules = self._load_json_rules("./json/post_code_enhancement.json")
        self.review_advice = self._load_json_rules("./json/know_review_advice.json")

    def _load_json_rules(self, file_path: str) -> Dict[str, List[str]]:
        if not os.path.exists(file_path):
            return {"data_retrieval": [], "data_analysis": []}
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def apply_pre_enhancement(self, step_type: str, step_content: str, prompt: str) -> str:
        """应用事前增强规则"""
        rules = self.pre_enhancement_rules.get(step_type, [])
        if not rules:
            return prompt  # 如果没有规则，直接返回原始提示词

        llm_prompt = f"""
        根据以下步骤内容和规则，判断是否有适用的规则来增强代码生成提示。
        如果没有适用的规则，请直接回答"无适用规则"。
        如果有适用的规则，请提供增强后的提示。

        步骤内容：{step_content}

        规则：
        {json.dumps(rules, ensure_ascii=False, indent=2)}

        原始提示：
        {prompt}

        请判断并给出结果。
        """

        response = self.llm_client.one_chat(llm_prompt)
        if "无适用规则" not in response:
            return response
        return prompt

    def apply_post_enhancement(self, step_type: str, step_content: str, code: str) -> str:
        """应用事后增强规则"""
        rules = self.post_enhancement_rules.get(step_type, [])
        if not rules:
            return code  # 如果没有规则，直接返回原始代码

        llm_prompt = f"""
        根据以下步骤内容、规则和生成的代码，判断是否有适用的规则来增强代码。
        如果没有适用的规则，请直接回答"无适用规则"。
        如果有适用的规则，请提供增强后的代码。

        步骤内容：{step_content}

        规则：
        {json.dumps(rules, ensure_ascii=False, indent=2)}

        生成的代码：
        {code}

        请判断并给出结果。
        增强后的代码必须是完整的代码，而不是增量修改片段。
        输出的代码用```python 和 ```包裹。
        """

        response = self.llm_client.one_chat(llm_prompt)
        if "无适用规则" not in response:
            return response
        return code

    def review_code(self, code: str, step_type: str) -> Generator[Dict[str, Any], None, None]:
        """审查代码并提供改进建议"""
        advice = self.review_advice.get(step_type, [])
        advice_str = "\n".join(f"- {item}" for item in advice)

        review_prompt = f"""
        请审查以下代码并提供改进建议，重点关注：
        1. 代码的可读性和可维护性
        2. 性能优化
        3. 最佳实践和常见陷阱
        4. 特定领域的考虑（例如，数据分析中的数据清洗，可视化中的美观性）

        同时，请特别注意以下与当前任务类型（{step_type}）相关的建议：
        {advice_str}

        如果代码已经很好，没有明显需要改进的地方，请直接回答"代码质量良好，无需改进"。

        代码：
        {code}

        请提供具体的改进建议，并解释原因。如果没有改进建议，请说明原因。
        """
        
        no_improvement_needed = False
        for chunk in self.llm_client.text_chat(review_prompt, is_stream=True):
            if "代码质量良好" in chunk and "无需改进" in chunk:
                no_improvement_needed = True
                break
            yield {"type": "code_review", "content": chunk}
        
        if no_improvement_needed:
            yield {"type": "code_review", "content": "代码审查完成，未发现需要改进的地方。"}