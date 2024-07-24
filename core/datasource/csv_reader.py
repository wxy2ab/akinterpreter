import pandas as pd
from ._file_reader import FileReader

class CsvReader(FileReader):
    def read_file(self):
        self.content = pd.read_csv(self.file_path)
        self.summary = self.generate_summary(self.content)

    def generate_summary(self, df):
        summary = f"行数: {df.shape[0]}\n"
        summary += f"列数: {df.shape[1]}\n"
        summary += f"列名: {', '.join(df.columns)}\n"
        summary += "前几行数据:\n"
        summary += df.head().to_string(index=False) + "\n"
        return summary

# # 使用示例
# csv_reader = CsvReader("example.csv")
# csv_reader.read_csv()

# table = csv_reader.get_table()
# summary = csv_reader.get_summary()

# print("摘要信息:\n")
# print(summary)

# # 若要查看表格的数据
# print("表格数据:\n")
# print(table)