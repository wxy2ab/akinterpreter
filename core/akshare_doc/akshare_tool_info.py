import inspect
from typing import List, Dict
import json
import os
import akshare as ak
from ..llms._llm_api_client import LLMApiClient
from ..llms.llm_factory import LLMFactory

class AkshareToolInfo:
    def __init__(self) -> None:
        factory = LLMFactory()
        self.llm:LLMApiClient = factory.get_instance()
        self.tools: List[Dict] = []
        self.json_file = "akshare_tools.json"
        self.load_tools_from_json()

    def load_tools_from_json(self):
        if os.path.exists(self.json_file):
            print(f"正在从 {self.json_file} 加载现有工具信息")
            with open(self.json_file, 'r', encoding='utf-8') as f:
                self.tools = json.load(f)
            print(f"已加载 {len(self.tools)} 个现有工具")
        else:
            print(f"未找到现有的 {self.json_file} 文件。将创建新文件。")

    def save_tools_to_json(self):
        print(f"正在将 {len(self.tools)} 个工具保存到 {self.json_file}")
        with open(self.json_file, 'w', encoding='utf-8') as f:
            json.dump(self.tools, f, ensure_ascii=False, indent=2)
        print("保存完成")

    def extract_akshare_functions(self) -> List[Dict]:
        print("正在从 akshare 库中提取函数...")
        functions = []
        for name, obj in inspect.getmembers(ak):
            if inspect.isfunction(obj):
                doc = inspect.getdoc(obj)
                if doc:
                    functions.append({"name": name, "docstring": doc})
        print(f"已提取 {len(functions)} 个带有文档字符串的函数")
        return functions

    def generate_tool_info(self, func_info: Dict) -> str:
        print(f"正在为函数生成工具信息: {func_info['name']}")
        prompt = f"""
        根据以下来自 akshare 库的函数信息：
        
        函数名称: {func_info['name']}
        文档字符串: {func_info['docstring']}
        
        生成一个符合 Claude API 函数调用规则的函数描述。描述应该使用以下格式，并且所有内容均使用中文：
        {{
            "name": "函数名称",
            "description": "函数功能的简要描述",
            "input_schema": {{
                "type": "object",
                "properties": {{
                    "参数1": {{
                        "type": "string",
                        "description": "参数1的描述"
                    }},
                    // 根据需要添加更多参数
                }},
                "required": ["必需的参数"]
            }}
        }}
        
        确保描述简洁准确，input_schema 正确反映了函数的参数，output_schema 描述了函数的返回值。所有描述和说明都应该使用中文。
        只返回 JSON 字符串，不要包含任何其他解释或说明。
        """
        result = self.llm.one_chat(prompt)
        print(f"生成的工具信息: {result}")
        return result

    def process_akshare_functions(self):
        functions = self.extract_akshare_functions()
        total_functions = len(functions)
        processed_functions = 0
        new_functions = 0

        print(f"开始处理 {total_functions} 个 akshare 函数")
        for func in functions:
            processed_functions += 1
            if not any(tool['name'] == func['name'] for tool in self.tools):
                tool_info_str = self.generate_tool_info(func)
                try:
                    tool_info = json.loads(tool_info_str)
                    self.tools.append(tool_info)
                    new_functions += 1
                except json.JSONDecodeError:
                    print(f"警告：函数 {func['name']} 的工具信息格式不正确，已跳过")
            
            if processed_functions % 10 == 0 or processed_functions == total_functions:
                print(f"进度: 已处理 {processed_functions}/{total_functions} 个函数，新增 {new_functions} 个工具")

        print(f"处理完成。总共新增工具数: {new_functions}")
        self.save_tools_to_json()

    def get_tools(self) -> List[Dict]:
        return self.tools

# 使用示例:
# ati = AkshareToolInfo()
# ati.process_akshare_functions()
# tools = ati.get_tools()