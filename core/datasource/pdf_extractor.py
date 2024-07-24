import PyPDF2
import pdfplumber
import io
import base64
import pandas as pd
from PIL import Image

from ._file_reader import FileReader

class PdfExtractor(FileReader):
    def read_file(self):
        with pdfplumber.open(self.file_path) as pdf:
            for page in pdf.pages:
                # 提取文本
                text = page.extract_text()
                if text:
                    self.content.append({"type": "text", "content": text})

                # 提取表格
                tables = page.extract_tables()
                for table in tables:
                    df = pd.DataFrame(table[1:], columns=table[0])
                    self.content.append({"type": "table", "content": df})

        self.summary = self.generate_summary()

    def generate_summary(self, total_length):
        content_count = len(self.content)
        summary = f"内容数量: {content_count}\n"
        summary += f"总长度: {total_length}\n"
        return summary

# # 使用示例
# pdf_extractor = PdfExtractor("example.pdf")
# pdf_extractor.extract()
# content = pdf_extractor.get_content()

# for item in content:
#     if item["type"] == "text":
#         print("Text Content:", item["content"])
#     elif item["type"] == "table":
#         print("Table Content:")
#         print(item["content"])
#     elif item["type"] == "image":
#         print("Image Content (Base64):", item["content"])