import os
import json
import re
from ..llms._llm_api_client import LLMApiClient
from ..llms.llm_factory import LLMFactory


def extract_interface_docs(content):
    sections = re.split(r'\n#{2,4}\s', content)
    
    interface_docs = []
    for section in sections:
        if re.search(r'^(.+?)\n+接口:', section, re.MULTILINE):
            lines = section.split('\n')
            interface_name = lines[0].strip()
            
            interface_info = {
                '接口名称': interface_name,
                '原文': section.strip()
            }
            current_field = None
            for line in lines[1:]:
                if line.startswith('接口:'):
                    current_field = '接口'
                    interface_info[current_field] = line.split(':', 1)[1].strip()
                elif line.startswith('描述:'):
                    current_field = '描述'
                    interface_info[current_field] = line.split(':', 1)[1].strip()
                elif line.startswith('限量:'):
                    current_field = '限量'
                    interface_info[current_field] = line.split(':', 1)[1].strip()
                elif line.startswith('输入参数'):
                    current_field = '输入参数'
                    interface_info[current_field] = ''
                elif line.startswith('输出参数'):
                    current_field = '输出参数'
                    interface_info[current_field] = ''
                elif line.startswith('接口示例'):
                    current_field = '接口示例'
                    interface_info[current_field] = ''
                elif line.startswith('数据示例'):
                    current_field = '数据示例'
                    interface_info[current_field] = ''
                elif current_field in ['输入参数', '输出参数', '接口示例', '数据示例']:
                    interface_info[current_field] += line + '\n'
            
            if all(key in interface_info for key in ['接口', '描述']):
                interface_docs.append(interface_info)
    
    return interface_docs

def simplify_docs(claude_client, docs):
    prompt = """Please simplify the following API documentation while retaining all necessary information for code generation. Preserve function names, descriptions, input and output parameters. Include information about rate limits if present. Summarize example code and data if provided, but don't remove them entirely. Remove any URLs or target addresses. Here's the documentation to simplify:

{docs}

Provide only the simplified documentation in your response, without any additional commentary. Maintain the original structure with headers for each section (e.g., '接口:', '描述:', '输入参数:', etc.), but omit the '目标地址:' section entirely."""

    response = claude_client.one_chat(prompt.format(docs=docs))
    return response.strip()

def process_markdown_files1(root_dir, claude_client):
    akshare_docs = {}
    
    if os.path.exists('akshare_docs.json'):
        with open('akshare_docs.json', 'r', encoding='utf-8') as f:
            akshare_docs = json.load(f)
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.endswith('.md'):
                filepath = os.path.join(dirpath, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                interface_docs = extract_interface_docs(content)
                for doc in interface_docs:
                    function_name = doc['接口']
                    
                    if function_name in akshare_docs:
                        print(f"Skipping {function_name} - already processed")
                        continue
                    
                    print(f"Processing {function_name}")
                    simplified_docs = simplify_docs(claude_client, doc['原文'])
                    akshare_docs[function_name] = simplified_docs
                    
                    with open('akshare_docs.json', 'w', encoding='utf-8') as f:
                        json.dump(akshare_docs, f, ensure_ascii=False, indent=2)
                
                if not interface_docs:
                    print(f"No interface documentation found in {filepath}")

def parse_akshare_docs(content):
    # 删除包含 "目标地址:" 的行
    content = re.sub(r'^目标地址:.*\n', '', content, flags=re.MULTILINE)

    # 使用正则表达式匹配接口名称和对应的文档内容 (删除前后#号限制)
    pattern = r'\n\n接口:\s*(\w+)([\s\S]*?)(?=(\n\n接口:|$))'
    matches = re.finditer(pattern, content)

    result = {}
    for match in matches:
        interface_name = match.group(1).strip()  # 接口名称
        doc_content = match.group(2).strip()    # 文档内容
        result[interface_name] = doc_content

    return result

def process_markdown_files(directory):
    all_docs = {}
    for root, dirs, files in os.walk(directory):
        for filename in files:
            if filename.endswith('.md'):
                file_path = os.path.join(root, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as file:
                        content = file.read()
                    parsed_docs = parse_akshare_docs(content)
                    all_docs.update(parsed_docs)
                    print(f"Processed: {file_path}")
                except Exception as e:
                    print(f"Error processing {file_path}: {str(e)}")
    return all_docs

def process_all():
    # 处理 ./docs 目录及其所有子目录下的 .md 文件
    docs_directory = './docs'
    parsed_docs = process_markdown_files(docs_directory)

    # 将结果保存为JSON文件
    output_file = 'akshare_docs.json'
    with open(output_file, 'w', encoding='utf-8') as json_file:
        json.dump(parsed_docs, json_file, ensure_ascii=False, indent=2)

    print(f"文档解析完成，结果已保存到 {output_file}")
    print(f"共处理了 {len(parsed_docs)} 个接口")

def check_doc():
    import json

    # 读取JSON文件
    with open('akshare_docs.json', 'r', encoding='utf-8') as file:
        data = json.load(file)

    # 用于存储有问题的key
    problematic_keys = []

    # 遍历字典中的每个键值对
    for key, value in data.items():
        # 查找value中接口后面的字符串
        start_index = value.find("接口: ")
        if start_index != -1:
            start_index += len("接口: ")
            end_index = value.find("\n", start_index)
            if end_index == -1:
                end_index = len(value)
            interface_name = value[start_index:end_index].strip()
            
            # 检查key是否与接口后面的字符串相同
            if key != interface_name:
                problematic_keys.append(key)

    # 输出有问题的key
    if problematic_keys:
        print("以下key与value中的接口名称不匹配:")
        for key in problematic_keys:
            print(key)
    else:
        print("所有key与value中的接口名称匹配。")
    
def truncate_functions(functions, max_length=28000):
    """截断函数列表，确保总字符数不超过max_length"""
    total_length = 0
    truncated_functions = []
    for func in functions:
        if total_length + len(func) + 1 > max_length:
            break
        truncated_functions.append(func)
        total_length += len(func) + 1  # +1 for newline
    return truncated_functions

def generate_summary(claude, functions, category):
    truncated_funcs = truncate_functions(functions)
    functions_text = "\n".join(truncated_funcs)
    prompt = f"""给定以下AKShare库中{category}类别的函数列表：

{functions_text}

请生成一个简洁的摘要，精确描述这些函数的核心功能和主要数据类型。摘要应：
1. 直接列举函数能够获取或处理的具体数据和信息
2. 使用关键词和术语，有助于快速识别该类别的特点
3. 避免使用笼统的描述，如"全面的"、"各种"等
4. 不提及数据来源
5. 不超过100个字

摘要:"""
    try:
        response = claude.one_chat(prompt)
        return response.strip()
    except Exception as e:
        print(f"生成{category}类别摘要时发生错误: {str(e)}")
        return f"无法生成{category}类别的摘要。"

def make_classified_summary():
    factory = LLMFactory()
    client = factory.get_instance()
    from ..akshare_doc.akshare_data_singleton import AKShareDataSingleton
    doc= AKShareDataSingleton()
    summaries = {}
    
    for category, functions in doc.classified_functions.items():
        print(f"正在处理类别: {category}")
        summary = generate_summary(client, functions, category)
        summaries[category] = summary
    
    # 保存结果到JSON文件
    with open('classified_summary_akshare.json', 'w', encoding='utf-8') as f:
        json.dump(summaries, f, ensure_ascii=False, indent=2)
    
    print("摘要已生成并保存到 classified_summary_akshare.json")


def main():
    factory = LLMFactory()
    llm_client:LLMApiClient = factory.get_instance()
    process_markdown_files('./docs/')

if __name__ == "__main__":
    main()