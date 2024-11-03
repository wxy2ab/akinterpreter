from typing import Union, Dict, List, Any
import json
import re
from core.llms.llm_factory import LLMFactory

def extract_json_from_text(text: str, llm_client_name: str = "SimpleDeepSeekClient", max_attempts: int = 4) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    """
    从文本中提取JSON对象并返回字典或字典列表。仅在需要时使用LLM进行智能修复。

    Args:
        text (str): 包含JSON数据的字符串
        llm_client_name (str): LLM客户端名称，默认为"SimpleDeepSeekClient"
        max_attempts (int): 最大修复尝试次数，默认为4

    Returns:
        Union[Dict[str, Any], List[Dict[str, Any]]]: 解析后的JSON对象

    Raises:
        JSONDecodeError: 如果在多次尝试后仍未能找到有效的JSON数据
    """
    def clean_json_string(json_str: str) -> str:
        """清理JSON字符串的基本问题"""
        # 替换单引号为双引号
        json_str = json_str.replace("'", '"')
        # 删除注释
        json_str = re.sub(r'//.*?\n|/\*.*?\*/', '', json_str, flags=re.S)
        # 清理多余的空白字符
        json_str = re.sub(r'\s+', ' ', json_str).strip()
        return json_str

    def fix_common_issues(json_str: str) -> str:
        """修复常见的JSON格式问题"""
        # 修复未加引号的键
        json_str = re.sub(r'(\w+)(?=\s*:)', r'"\1"', json_str)
        # 修复多余的逗号
        json_str = re.sub(r',\s*([}\]])', r'\1', json_str)
        # 修复缺少逗号的情况
        json_str = re.sub(r'([}\]"])\s*([{\["]\w+)', r'\1,\2', json_str)
        # 修复布尔值和null值
        json_str = re.sub(r'\btrue\b', 'true', json_str, flags=re.I)
        json_str = re.sub(r'\bfalse\b', 'false', json_str, flags=re.I)
        json_str = re.sub(r'\bnull\b', 'null', json_str, flags=re.I)
        # 修复数值
        json_str = re.sub(r'\b(\d+)L\b', r'\1', json_str)  # 移除长整型标记
        return json_str

    def extract_json_content(text: str) -> str:
        """从文本中提取可能的JSON内容"""
        patterns = [
            r'```json\s*([\s\S]*?)\s*```',  # Markdown JSON代码块
            r'`([\s\S]*?)`',                # 内联代码块
            r'\{[\s\S]*\}',                 # JSON对象
            r'\[[\s\S]*\]'                  # JSON数组
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                content = match.group(1) if '```json' in pattern or '`' in pattern else match.group(0)
                return content.strip()
        return text.strip()

    def attempt_json_parse(json_str: str) -> Union[Dict[str, Any], List[Dict[str, Any]], None]:
        """尝试解析JSON字符串"""
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            cleaned = clean_json_string(json_str)
            fixed = fix_common_issues(cleaned)
            try:
                return json.loads(fixed)
            except json.JSONDecodeError:
                return None

    def llm_fix_json(json_str: str, error: str) -> str:
        """使用LLM修复JSON，仅在需要时创建LLM实例"""
        llm_client = LLMFactory().get_instance(llm_client_name)
        prompt = f"""
        以下JSON字符串解析时发生错误。请修复这个JSON并确保它是有效的。
        如果看到类似Python字典的格式，请将其转换为有效的JSON格式。

        原始字符串：
        ```
        {json_str}
        ```

        错误信息：{error}

        修复规则：
        1. 保持原始数据结构和值不变
        2. 修复所有影响JSON有效性的问题：
           - 确保所有键都用双引号括起来
           - 修复未闭合的引号和括号
           - 删除或修复非法注释
           - 处理多余或缺失的逗号
           - 修复嵌套引号冲突
           - 确保布尔值使用小写(true/false)
           - 确保null使用小写
           - 移除任何Python特有的标记(如长整型L后缀)
        3. 不要添加新的内容或改变现有的值
        
        请只返回修复后的JSON，不要包含任何解释或额外标记。
        确保返回的是符合规范的JSON格式。
        """
        
        response = llm_client.one_chat(prompt)
        # 提取回答中的JSON内容
        return extract_json_content(response)

    # 主要处理逻辑
    json_str = extract_json_content(text)
    
    for attempt in range(max_attempts):
        result = attempt_json_parse(json_str)
        if result is not None:
            return result
            
        if attempt < max_attempts - 1:
            try:
                # 记录当前错误以供LLM参考
                try:
                    json.loads(json_str)
                except json.JSONDecodeError as e:
                    error = str(e)
                
                # 仅在常规修复失败时使用LLM
                json_str = llm_fix_json(json_str, error)
            except Exception as e:
                # 如果LLM修复失败，继续下一次尝试
                continue
    
    raise json.JSONDecodeError(f"Failed to parse JSON after {max_attempts} attempts", text, 0)
