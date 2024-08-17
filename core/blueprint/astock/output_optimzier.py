import re

class PromptOutputOptimizer:
    def __init__(self, llm_client):
        self.llm_client = llm_client

    def optimize(self, original_prompt: str, original_output: str, task_description: str, max_iterations: int = 5) -> str:
        current_output = original_output
        iteration = 0

        while iteration < max_iterations:
            # Step 1: Chain of Thought (COT)
            cot_prompt = f"""
            请对以下输出进行分析和改进，使用思维链（Chain of Thought）技术：

            原始任务描述: {task_description}

            原始提示词:
            {original_prompt}

            当前输出:
            {current_output}

            请执行以下步骤，并详细解释您的思考过程：

            1. 分析输出的每个部分，评估它如何满足原始任务的需求。
            2. 识别可能的改进点，如内容的准确性、完整性、逻辑性等。
            3. 考虑如何使输出更加清晰、全面和有效。
            4. 提出具体的改进建议。

            请提供详细的分析和建议。
            """

            cot_analysis = self.llm_client.one_chat(cot_prompt)

            # Step 2: Self-Reflection
            reflection_prompt = f"""
            请对以下思维链分析进行自我反思，并提出进一步的改进建议：

            原始任务描述: {task_description}

            原始提示词:
            {original_prompt}

            当前输出:
            {current_output}

            思维链分析:
            {cot_analysis}

            请执行以下步骤：

            1. 评估思维链分析的质量和完整性。
            2. 识别分析中可能存在的偏见或逻辑缺陷。
            3. 考虑是否有任何重要的角度或方法被忽视。
            4. 基于这些反思，提出额外的改进建议。
            5. 评估是否还需要进一步优化，如果认为当前输出已经足够好，请明确说明。

            请提供您的自我反思结果、改进建议，以及是否需要继续优化的结论。
            """

            reflection_result = self.llm_client.one_chat(reflection_prompt)

            # Check if further optimization is needed
            if "不需要进一步优化" in reflection_result or "当前输出已经足够好" in reflection_result:
                break

            # Step 3: Apply improvements
            improvement_prompt = f"""
            请基于原始任务、原始提示词、当前输出、思维链分析和自我反思的结果，生成一个优化后的输出：

            原始任务描述: {task_description}

            原始提示词:
            {original_prompt}

            当前输出:
            {current_output}

            思维链分析:
            {cot_analysis}

            自我反思和改进建议:
            {reflection_result}

            请生成一个优化后的输出，确保：
            1. 充分吸收思维链分析和自我反思中的有效建议
            2. 输出结构清晰，易于理解
            3. 全面覆盖原始任务的需求
            4. 保持与原始提示词的相关性
            5. 改进内容的准确性、完整性和逻辑性

            请直接提供优化后的输出，不要添加任何解释。
            """

            optimized_output = self.llm_client.one_chat(improvement_prompt)
            current_output = self._extract_content(optimized_output)

            iteration += 1

        return current_output

    def _extract_content(self, text: str) -> str:
        # Remove any markdown code blocks if present
        code_block_pattern = r'```[\s\S]*?```'
        text = re.sub(code_block_pattern, '', text)
        
        # Remove any remaining markdown formatting
        text = re.sub(r'[*#_~`]', '', text)
        
        return text.strip()