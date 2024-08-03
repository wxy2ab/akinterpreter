import json
import re
from bs4 import BeautifulSoup
import html2text

def html_to_markdown(html_content):
    h = html2text.HTML2Text()
    h.ignore_links = False
    return h.handle(html_content)

def extract_interface_docs():
    with open('./json/tushare_doc_full.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    interface_docs = {}

    for item in data:
        content = item['content']
        if '接口：' in content:
            soup = BeautifulSoup(content, 'html.parser')
            text = soup.get_text()

            # 提取接口名称（只允许英文）
            match = re.search(r'接口：([a-zA-Z_][a-zA-Z0-9_]*)', text)
            if match:
                function_name = match.group(1)

                # 提取描述部分
                description_start = text.find('描述：')
                if description_start != -1:
                    doc = text[description_start:]
                    
                    # 将HTML转换为Markdown
                    markdown_doc = html_to_markdown(content[content.find('描述：'):])
                    
                    interface_docs[function_name] = markdown_doc.strip()

    return interface_docs

def save_to_json(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    # 运行函数并保存结果
    interface_docs = extract_interface_docs()

    # 保存结果到新的JSON文件
    save_to_json(interface_docs, './json/tushare_docs.json')

    print("接口文档提取完成，已保存到 ./json/tushare_docs.json")