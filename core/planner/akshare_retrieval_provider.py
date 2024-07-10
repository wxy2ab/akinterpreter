import re
from typing import Dict, List
from core.akshare_doc.akshare_data_singleton import AKShareDataSingleton


class AkshareRetrievalProvider:
    def __init__(self):
        self.data_singleton = AKShareDataSingleton()
        self.category_summaries = self.data_singleton.get_category_summaries()
        self.classified_functions = self.data_singleton.get_classified_functions()
        self.akshare_docs = self.data_singleton.get_akshare_docs()


    def get_categories(self) -> Dict[str, str]:
        """
        返回可用的数据类别字典
        :return: 字典，键为类别名称，值为类别描述
        """
        return self.category_summaries

    def get_functions(self, categories: List[str]) -> Dict[str, List[str]]:
        """
        根据给定的类别返回相关函数
        :param categories: 类别列表
        :return: 字典，键为类别，值为该类别下的函数列表
        """
        result = {}
        for category in categories:
            if category in self.classified_functions:
                functions = self.classified_functions[category]
                result[category] = [self._extract_function_name(func) for func in functions]
        return result

    def _extract_function_name(self, function_string: str) -> str:
        """
        从函数字符串中提取函数名
        :param function_string: 包含函数名和描述的字符串
        :return: 函数名
        """
        match = re.match(r"(\w+):", function_string)
        if match:
            return match.group(1)
        else:
            # 如果无法提取函数名，返回整个字符串
            return function_string

    def get_specific_doc(self, functions: List[str]) -> Dict[str, str]:
        """
        获取指定函数的文档
        :param functions: 函数名列表
        :return: 字典，键为函数名，值为对应的文档
        """
        return {func: self.akshare_docs.get(func, "Documentation not available") for func in functions}
