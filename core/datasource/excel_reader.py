import pandas as pd

from ._file_reader import FileReader

class ExcelReader(FileReader):
    def read_file(self):
        self.content = pd.read_excel(self.file_path, sheet_name=None)
        summary_list = []
        for sheet_name, df in self.content.items():
            summary_list.append(self.generate_summary(sheet_name, df))
        self.summary = "\n\n".join(summary_list)

    def generate_summary(self, sheet_name, df):
        summary = f"工作表名称: {sheet_name}\n"
        summary += f"行数: {df.shape[0]}\n"
        summary += f"列数: {df.shape[1]}\n"
        summary += f"列名: {', '.join(df.columns)}\n"
        summary += "前几行数据:\n"
        summary += df.head().to_string(index=False) + "\n"
        return summary


# # 使用示例
# excel_reader = ExcelReader("example.xlsx")
# excel_reader.read_excel()

# tables = excel_reader.get_tables()
# summaries = excel_reader.get_summaries()

# print("摘要信息:\n")
# print(summaries)

# # 若要查看某个表格的数据
# # print(tables["SheetName"])