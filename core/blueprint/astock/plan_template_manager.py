import json
import re
from typing import List, Dict, Optional
from core.llms._llm_api_client import LLMApiClient

class PlanTemplateManager:
    def __init__(self, llm_client: LLMApiClient):
        self.llm_client = llm_client
        self.templates: List[Dict] = []
        self.default_template: Dict = {
            "description": "默认通用模板",
            "template": """
            1. 分析查询需求：
            - 这个查询的主要目标是什么？
            - 需要哪些具体的数据来回答这个查询？

            2. 关键要点
            - 不考虑数据的前提下，这个查询需求的要点是什么？

            3. 确定数据获取步骤：
            - 根据查询需求，需要调用哪些数据提供函数？
            - 这些函数的调用顺序应该如何安排？

            4. 设计数据处理逻辑：
            - 获取的数据需要进行哪些处理或转换？
            - 是否需要进行数据过滤、排序或聚合？

            5. 构建LLM分析提示词：
            - 提示词应该包含哪些关键信息？
            - 如何确保提示词清晰、具体且全面？
            - 如何在提示词中指定输出格式和评价标准？
            - 如何设计提示词才能符合第二步的查询需求要点？

            6. 结果呈现：
            - 最终结果应该以什么格式呈现？
            - 如何确保结果易于理解和使用？

            注意，请确保在处理 LLM 返回结果时：
            1. 提示词中要求以JSON格式返回结果。
            2. 提示词中要求明确的数据结构。
            3. 检查所有必要的字段是否存在。
            4. 对于无法解析的结果，添加适当的错误处理逻辑。
            5. 考虑添加重试机制，在失败时重新构建提示词并再次请求 LLM。
            """
        }

    def add_template(self, description: str, template: str):
        self.templates.append({
            "description": description,
            "template": template
        })

    def load_templates_from_file(self, file_path: str):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 将内容分割成多个部分
        sections = re.split(r'(?m)^###\s*', content)[1:]  # 跳过第一个空白分割
        
        self.templates = []
        for section in sections:
            lines = section.strip().split('\n')
            description = lines[0].strip()
            template = '\n'.join(lines[1:]).strip()
            self.add_template(description, template)

    def save_templates_to_file(self, file_path: str):
        with open(file_path, 'w', encoding='utf-8') as f:
            for template in self.templates:
                f.write(f"### {template['description']}\n")
                f.write(f"{template['template']}\n\n")

    def get_best_template(self, query: str) -> Optional[Dict]:
        prompt = f"""
        根据以下查询：
        {query}

        以及以下计划模板描述列表：
        {json.dumps([t['description'] for t in self.templates], ensure_ascii=False, indent=2)}

        请选择最适合该查询的模板。你的回答应该是一个JSON格式的字符串，包含以下字段：
        1. "index": 最佳匹配模板的索引（从0开始的整数）。如果没有合适的模板，请返回-1。
        2. "reason": 选择这个模板或返回-1的原因（字符串）

        请确保你的回答是一个有效的JSON字符串，并用```json和```包裹。
        示例回答格式：
        ```json
        {{
            "index": 0,
            "reason": "这个模板最适合因为..."
        }}
        ```
        或者
        ```json
        {{
            "index": -1,
            "reason": "没有完全匹配的模板，因为..."
        }}
        ```
        """
        response = self.llm_client.one_chat(prompt)
        
        try:
            # 提取JSON字符串
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if not json_match:
                raise ValueError("回答中没有找到JSON格式的内容")
            
            json_str = json_match.group(1)
            result = json.loads(json_str)
            
            index = result['index']
            if index == -1:
                print(f"没有找到合适的模板。原因: {result['reason']}")
                return None
            
            if not isinstance(index, int) or index < 0 or index >= len(self.templates):
                raise ValueError(f"无效的模板索引: {index}")
            
            return self.templates[index]
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"解析模板选择时出错: {str(e)}")
            return None

    def get_template(self, query: str) -> Dict:
        template = self.get_best_template(query)
        return template if template is not None else self.default_template
