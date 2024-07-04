import json
import os

def convert_json_to_python(json_file_path, output_file_path):
    # 读取 JSON 文件
    with open(json_file_path, 'r', encoding='utf-8') as json_file:
        data = json.load(json_file)

    # 准备输出内容
    output_content = 'akshare_all_functions:str="""\n'

    # 处理每个函数
    for item in data:
        function_name = item.get('name', '')
        description = item.get('description', '').replace('\n', ' ')  # 移除描述中的换行符
        output_content += f'"{function_name}",  # {description}\n'

    output_content += '"""'

    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

    # 写入输出文件
    with open(output_file_path, 'w', encoding='utf-8') as output_file:
        output_file.write(output_content)

    print(f"File generated successfully: {output_file_path}")


def convert_json_array_to_dict(input_file: str, output_file: str):
    # 读取输入 JSON 文件
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 确保输入数据是一个列表
    if not isinstance(data, list):
        raise ValueError("Input JSON is not an array")

    # 将数组转换为字典，使用 'name' 字段作为键
    data_dict = {item['name']: item for item in data}

    # 将转换后的字典写入输出 JSON 文件
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data_dict, f, ensure_ascii=False, indent=2)

    print(f"Conversion completed. Dictionary saved to {output_file}")
# 使用函数
# json_file_path = 'akshare_tools.json'
# output_file_path = './core/all_akshare_function.py'

# convert_json_to_python(json_file_path, output_file_path)