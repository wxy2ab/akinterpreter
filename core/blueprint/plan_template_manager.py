import json
import re
from typing import List, Dict, Optional
from core.llms._llm_api_client import LLMApiClient

class PlanTemplateManager:
    def __init__(self, llm_client: LLMApiClient):
        self.llm_client = llm_client
        self.templates: List[Dict] = []
        self.default_template: Dict = {}

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