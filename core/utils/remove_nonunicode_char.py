import json

def remove_invalid_chars(input_file):
    try:
        # 使用UTF-8编码读取文件，忽略错误
        with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # 尝试解析JSON
        data = json.loads(content)
        
        # 如果解析成功，将清理后的数据写入新文件
        with open(input_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        
        print(f"文件已清理并保存为 {input_file}")
    
    except json.JSONDecodeError as e:
        print(f"JSON解析错误: {e}")
        print("尝试手动清理文件内容...")
        
        # 如果JSON解析失败，尝试手动清理内容
        cleaned_content = ''.join(char for char in content if ord(char) < 128)
        
        with open(input_file, 'w', encoding='utf-8') as f:
            f.write(cleaned_content)
        
        print(f"文件已清理并保存为 {input_file}，但可能需要手动检查JSON格式")

