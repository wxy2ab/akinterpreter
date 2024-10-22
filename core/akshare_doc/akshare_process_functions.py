

import json
import re
import akshare as ak
import inspect
from typing import Dict, List

from core.llms._llm_api_client import LLMApiClient

"""
    #process akshare functions

    from core.akshare_doc.akshare_process_functions import AkShareProcessFunctions
    from core.llms.llm_factory import LLMFactory
    #write all akshare functions to a file
    funs = AkShareProcessFunctions()
    funs.write_full_sting("./core/akshare_doc/all_akshare_function.py")

    factory = LLMFactory()
    llm = factory.get_instance()
    funs = AkShareProcessFunctions()
    from core.akshare_doc.all_akshare_function import all_functions
    cf = funs.classify_akshare_functions(all_functions,llm)
    funs.save_classified_functions(cf,"./json/classified_akshare_functions.json")
"""

class AkShareProcessFunctions:
    def __init__(self) -> None:
        pass
    def extract_akshare_functions(self) -> List[Dict]:
        print("正在从 akshare 库中提取函数...")
        functions = []
        for name, obj in inspect.getmembers(ak):
            if inspect.isfunction(obj):
                doc = inspect.getdoc(obj)
                if doc:
                    functions.append({"name": name, "docstring": doc.splitlines()[0]})
        print(f"已提取 {len(functions)} 个带有文档字符串的函数")
        return functions
    
    def get_full_functions_string(self)->str:
        functions = self.extract_akshare_functions()
        functions_str = "".join([f"{func['name']}: {func['docstring']}\n" for func in functions if "http" not in func['docstring']])
        return functions_str
    
    def write_full_sting(self,file_path:str):
        """
        self.write_full_sting("./core/akshare_doc/all_akshare_function.py")
        """
        functions_str = self.get_full_functions_string()
        all_string=f"""
all_functions = \"\"\"
{functions_str}
\"\"\"
"""
        with open(file_path, "w", encoding='utf-8') as f:
            f.write(all_string)
        print(f"已将函数文档字符串写入到 {file_path}")

    def classify_akshare_functions(self,akshare_all_functions: str, llm_client: LLMApiClient) -> Dict[str, List[str]]:
        from core.akshare_doc.akshare_data_singleton import AKShareDataSingleton
        singleton = AKShareDataSingleton()
        categories_summary = singleton.category_summaries
        summary = "\n".join([f"{k}: {v}" for k, v in categories_summary.items()])
        # 定义主要分类
        categories = [
            "股票数据", "期货数据", "期权数据", "债券数据", "外汇数据", 
            "宏观经济数据", "基金数据", "指数数据", "另类数据", "新闻数据", 
            "港股数据", "美股数据", "金融工具", "数据工具", "行业数据",
            "公司数据", "交易所数据", "市场情绪数据", "其他数据"
        ]

        # VSCode 兼容的正则表达式
        pattern = r'^(\w+):\s*(.*?)(?=\n|$)'
        functions = re.findall(pattern, akshare_all_functions, re.MULTILINE)

        print(f"Total functions found: {len(functions)}")  # 打印找到的函数总数

        # 处理可能的多行描述
        processed_functions = []
        current_func = None
        current_desc = ""
        for func_name, desc in functions:
            if func_name:
                if current_func:
                    processed_functions.append((current_func, current_desc.strip()))
                current_func = func_name
                current_desc = desc
            else:
                current_desc += " " + desc.strip()
        if current_func:
            processed_functions.append((current_func, current_desc.strip()))

        print(f"Processed functions: {len(processed_functions)}")  # 打印处理后的函数总数

        classified_functions = {category: [] for category in categories}
        
        # 批量处理函数，每次处理50个
        batch_size = 50
        for i in range(0, len(processed_functions), batch_size):
            batch = processed_functions[i:i+batch_size]
            
            prompt = f"""
            请将以下函数根据其描述分类到最合适的类别中。对于每个函数，只返回类别名称，不要有任何其他文字。
            每行一个函数，格式为：函数名: 类别

            可选类别:
            {', '.join(categories)}

            类别描述：
            {summary}

            需要分类的函数：
            """
            
            for func_name, description in batch:
                prompt += f"{func_name}: {description}\n"

            response = llm_client.one_chat(prompt).strip()
            
            # 处理响应
            lines = response.split('\n')
            for line in lines:
                if ':' in line:
                    func_name, category = line.split(':', 1)
                    func_name = func_name.strip()
                    category = category.strip()
                    
                    if category in categories:
                        classified_functions[category].append(f"{func_name}: {dict(processed_functions)[func_name]}")
                    else:
                        classified_functions["其他数据"].append(f"{func_name}: {dict(processed_functions)[func_name]}")

            print(f"Processed batch {i//batch_size + 1} of {len(processed_functions)//batch_size + 1}")  # 打印处理进度

        return classified_functions

    def save_classified_functions(self,classified_functions: Dict[str, List[str]], file_path: str):
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(classified_functions, f, ensure_ascii=False, indent=2)

    # 打印分类结果
    def print_classified_functions(self,classified_functions: Dict[str, List[str]]):
        total_functions = 0
        for category, functions in classified_functions.items():
            print(f"\n{category} ({len(functions)} 个函数):")
            for func in functions[:5]:  # 只打印前5个函数作为示例
                print(f"  - {func}")
            if len(functions) > 5:
                print("  ...")
            total_functions += len(functions)
        print(f"\n总计: {total_functions} 个函数")
    