import requests
import json
from urllib.parse import urlparse
from typing import Optional, Dict, Any
from ..interpreter.ast_code_runner import ASTCodeRunner
from core.llms._llm_api_client import LLMApiClient

class UrlReader:
    """
    用于读取URL内容的阅读器,使用LLM辅助提取和错误修正。
    使用基于域名的缓存来存储成功的提取代码。
    """
    def __init__(self, llm_client:LLMApiClient):
        self._code_cache_file = "./json/reader_extraction_code_cache.json"
        self.llm_client = llm_client
        self.max_retries = 3
        self.code_runner = ASTCodeRunner()
        self.extraction_code_cache = {}
        self._load_extraction_code_cache()

    def read(self, url: str) -> str:
        """
        读取URL的内容并使用LLM提取主要文档。
        
        参数:
            url (str): 要读取的URL。
        返回:
            str: 提取的文档内容。
        """
        raw_content = self._fetch_url_content(url)
        domain = self._get_domain(url)
        
        # 尝试使用缓存的代码
        if domain in self.extraction_code_cache:
            try:
                document_content = self._execute_extraction(self.extraction_code_cache[domain], raw_content)
                if document_content:
                    return document_content
            except Exception:
                # 如果缓存的代码失败，从缓存中移除并继续生成新代码
                del self.extraction_code_cache[domain]

        extraction_code = self._generate_extraction_code(raw_content)
        document_content = self._execute_extraction(extraction_code, raw_content)
        
        # 如果成功提取内容，保存代码到缓存
        if document_content:
            self.extraction_code_cache[domain] = extraction_code
            self._save_extraction_code_cache()  # 保存缓存到文件
        
        return document_content

    def _get_domain(self, url: str) -> str:
        """从URL中提取域名。"""
        return urlparse(url).netloc

    def _fetch_url_content(self, url: str) -> str:
        """获取URL的原始内容。"""
        response = requests.get(url)
        response.raise_for_status()
        return response.text

    def _generate_extraction_code(self, content: str) -> str:
        """使用LLM生成代码来提取主要文档内容。"""
        prompt = f"""
        HTML内容:
        {content[:5000]}

        生成Python代码来提取HTML内容中的主要文档内容。
        移除无关的部分,如页眉、页脚、导航等。
        只保留主要文档文本。
        移除Html标签，用Markdown格式输出文档内容

        请注意以下要求：
        1. HTML内容通过调用 get_content() 函数获取。这个函数已经定义好，不需要你实现。
        2. 你的代码应该使用 get_content() 函数来获取内容。
        3. 提取的主要文本应该存储在名为 'extracted_content' 的变量中。
        4. 不要定义或重写 get_content() 函数。
        5. 请将生成的代码用 ```python 和 ``` 包裹。

        这里有一个示例代码结构供参考：

        ```python
        from bs4 import BeautifulSoup

        # 获取HTML内容
        html_content = get_content()

        # 使用BeautifulSoup解析HTML
        soup = BeautifulSoup(html_content, 'html.parser')

        # 提取主要内容的逻辑
        # ...

        # 存储提取的内容
        extracted_content = "提取的主要内容"
        ```

        请基于这个结构生成完整的提取代码：
        """
        response = self.llm_client.one_chat(prompt)
        # 提取被 ```python 和 ``` 包裹的代码
        start = response.find("```python") + 10
        end = response.rfind("```")
        return response[start:end].strip()

    def _execute_extraction(self, code: str, content: str) -> str:
        """执行生成的代码来提取文档内容。"""
        def get_content():
            return content

        global_vars = {"get_content": get_content}
        for _ in range(self.max_retries):
            try:
                result = self.code_runner.run(code, global_vars)
                if result.get("error"):
                    raise Exception(result["error"])
                extracted_content = result["updated_vars"].get("extracted_content", "")
                if not extracted_content:
                    raise Exception("提取的内容为空")
                return extracted_content
            except Exception as e:
                code = self._fix_code(code, str(e))
        raise Exception("达到最大重试次数。无法提取内容。")

    def _fix_code(self, code: str, error: str) -> str:
        """使用LLM基于错误消息修复代码。"""
        prompt = f"""
        以下代码在处理HTML内容时遇到了一个错误:

        当前代码:
        ```python
        {code}
        ```

        错误信息:
        {error}

        请修复此代码以解决这个错误。使用以下步骤:
        1. 分析错误信息。
        2. 确定错误的可能原因。
        3. 提出解决方案。
        4. 在代码中实现修复。
        5. 反思这个修复是否可能解决问题。

        请注意以下要求：
        1. HTML内容通过调用 get_content() 函数获取。这个函数已经定义好，不需要你实现或修改。
        2. 你的代码应该使用 get_content() 函数来获取内容。
        3. 提取的主要文本应该存储在名为 'extracted_content' 的变量中。
        4. 不要定义或重写 get_content() 函数。
        5. 请将修正后的代码用 ```python 和 ``` 包裹。

        这里有一个示例代码结构供参考：

        ```python
        from bs4 import BeautifulSoup

        # 获取HTML内容
        html_content = get_content()

        # 使用BeautifulSoup解析HTML
        soup = BeautifulSoup(html_content, 'html.parser')

        # 提取主要内容的逻辑
        # ...

        # 存储提取的内容
        extracted_content = "提取的主要内容"
        ```

        请基于这个结构修复代码：
        """
        response = self.llm_client.one_chat(prompt)
        # 提取被 ```python 和 ``` 包裹的代码
        start = response.find("```python") + 10
        end = response.rfind("```")
        return response[start:end].strip()

    def _save_extraction_code_cache(self):
        """保存提取代码缓存到文件。"""
        with open(self._code_cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.extraction_code_cache, f)

    def _load_extraction_code_cache(self):
        """从文件加载提取代码缓存。"""
        try:
            with open(self._code_cache_file, 'r', encoding='utf-8') as f:
                self.extraction_code_cache = json.load(f)
        except FileNotFoundError:
            self.extraction_code_cache = {}