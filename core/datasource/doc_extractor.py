import docx
import base64
import pandas as pd
from io import BytesIO
from PIL import Image

from ._file_reader import FileReader

class DocExtractor(FileReader):
    def read_file(self):
        doc = docx.Document(self.file_path)
        
        for element in doc.element.body:
            if element.tag.endswith('p'):
                para = docx.text.paragraph.Paragraph(element, doc)
                if para.text.strip():
                    self.content.append({"type": "text", "content": para.text})
            elif element.tag.endswith('tbl'):
                table = docx.table.Table(element, doc)
                data = []
                keys = None
                for i, row in enumerate(table.rows):
                    text = [cell.text.strip() for cell in row.cells]
                    if i == 0:
                        keys = text
                    else:
                        data.append(text)
                if keys and data:
                    df = pd.DataFrame(data, columns=keys)
                    self.content.append({"type": "table", "content": df})

        for rel in doc.part.rels.values():
            if "image" in rel.target_ref:
                image_data = rel.target_part.blob
                image_base64 = base64.b64encode(image_data).decode('utf-8')
                self.content.append({"type": "image", "content": image_base64})

        self.summary = self.generate_summary()

    def generate_summary(self, total_length):
        content_count = len(self.content)
        summary = f"内容数量: {content_count}\n"
        summary += f"总长度: {total_length}\n"
        return summary

# # 使用示例
# doc_extractor = DocExtractor("example.docx")
# doc_extractor.extract()
# content = doc_extractor.get_content()

# for item in content:
#     if item["type"] == "text":
#         print("Text Content:", item["content"])
#     elif item["type"] == "table":
#         print("Table Content:")
#         print(item["content"])
#     elif item["type"] == "image":
#         print("Image Content (Base64):", item["content"])