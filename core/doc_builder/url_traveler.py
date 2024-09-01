import json
import os
import re
from typing import Callable, Any, Dict
from urllib.parse import urlparse
from ._traveler import Traveler
from core.llms._llm_api_client import LLMApiClient
from ..interpreter.ast_code_runner import ASTCodeRunner
from ._reader import Reader

class UrlTraveler(Traveler):
    """A Traveler implementation for traversing URL structures."""

    def __init__(self, reader: Reader, callback: Callable[[Any], Any], llm_client: LLMApiClient):
        """
        Initialize the UrlTraveler.

        Args:
            reader (Reader): An object responsible for reading the contents of URLs.
            callback (Callable[[Any], Any]): A function that will be called
                on the content read from each leaf URL.
            llm_client (LLMApiClient): The LLM API client for generating and correcting code.
        """
        super().__init__(reader, callback)
        self.llm_client = llm_client
        self.code_runner = ASTCodeRunner()
        self.code_cache_path = "./output/traveler_code_cache.json"
        self.max_retries = 5
        self._load_code_cache()

    def _load_code_cache(self):
        """Load the code cache from file."""
        if os.path.exists(self.code_cache_path):
            with open(self.code_cache_path, 'r') as f:
                self.code_cache = json.load(f)
        else:
            self.code_cache = {}

    def _save_code_cache(self):
        """Save the code cache to file."""
        os.makedirs(os.path.dirname(self.code_cache_path), exist_ok=True)
        with open(self.code_cache_path, 'w') as f:
            json.dump(self.code_cache, f)

    def _generate_traverse_code(self, url: str, content: str) -> str:
        """Generate code to traverse the URL structure using LLM."""
        prompt = f"""
        基于以下URL内容，生成一个实现'traverse'方法的Python代码，用于UrlTraveler类。
        该方法应返回一个字典列表，每个字典包含URL结构中每个节点的'uri'（字符串）和'is_leaf'（布尔值）。

        URL: {url}
        内容:
        {content[:10000]}  # 限制内容为前10000个字符

        代码应该：
        1. 解析内容以找到文档的目录结构。
        2. 返回格式为[{{'uri': '...', 'is_leaf': True/False}}, ...]的字典列表。
        3. 仅使用Python标准库。
        4. 不要加入错误处理代码。

        这里是一个代码示例，展示了我们期望的基本结构：

        ```python
        def traverse(url, content):
            result = []
            # 这里应该是解析content的逻辑
            # 示例：假设我们从content中提取了一些链接
            links = extract_links(content)  # 这个函数需要你来实现
            for link in links:
                full_url = urljoin(url, link)
                is_leaf = determine_if_leaf(link)  # 这个函数需要你来实现
                result.append({{'uri': full_url, 'is_leaf': is_leaf}})
            return result
        ```

        请基于上面的示例和给定的URL内容，实现完整的'traverse'方法。确保方法能够正确解析内容并返回适当的结果。
        不要包括类定义和导入语句。请使用```python ```包裹返回的代码。
        """
        response = self.llm_client.one_chat(prompt)
        return self._extract_code(response)

    def _extract_code(self, response: str) -> str:
        """Extract code from the LLM response."""
        match = re.search(r'```python\s*(.*?)\s*```', response, re.DOTALL)
        if match:
            return match.group(1)
        return response  # 如果没有找到包裹的代码，返回整个响应

    def _fix_code(self, url: str, content: str, code: str, error: str) -> str:
        """Fix the generated code based on the error message."""
        prompt = f"""
        之前为以下URL生成的代码出现了错误。请修复这段代码。

        URL: {url}
        内容:
        {content[:10000]}  # 限制内容为前10000个字符

        当前代码:
        ```python
        {code}
        ```

        错误信息:
        {error}

        请提供修复后的完整'traverse'方法代码。不要包括类定义和导入语句。请使用```python ```包裹返回的代码。
        """
        response = self.llm_client.one_chat(prompt)
        return self._extract_code(response)

    def _execute_traverse_code(self, code: str, url: str) -> list[dict]:
        """Execute the generated traverse code."""
        global_vars = {'url': url, 'content': self._reader.read(url)}
        result = self.code_runner.run(code, global_vars)
        
        if result['error']:
            raise Exception(f"Code execution error: {result['error']}")
        
        return result['updated_vars'].get('result', [])

    def traverse(self, url: str) -> list[dict]:
        """
        Traverse the URL structure starting from the given URL.

        Args:
            url (str): The root URL to start traversing from.

        Returns:
            list[dict]: A list of dictionaries, each containing:
                - 'uri': The URL of the node
                - 'is_leaf': Boolean indicating if the node is a leaf
        """
        domain = urlparse(url).netloc
        if domain in self.code_cache:
            try:
                return self._execute_traverse_code(self.code_cache[domain], url)
            except Exception:
                # If cached code fails, regenerate it
                pass

        content = self._reader.read(url)
        code = self._generate_traverse_code(url, content)

        for _ in range(self.max_retries):
            try:
                result = self._execute_traverse_code(code, url)
                self.code_cache[domain] = code
                self._save_code_cache()
                return result
            except Exception as e:
                code = self._fix_code(url, content, code, str(e))

        raise Exception(f"在{self.max_retries}次尝试后，未能为{url}生成有效的代码。")

    def traverse_all(self, url: str) -> list[Any]:
        """
        Recursively traverse all URLs starting from the given URL,
        process leaf nodes, and return the results.

        Args:
            url (str): The root URL to start traversing from.

        Returns:
            list[Any]: A list of processed results from all leaf URLs.
        """
        return super().traverse_all(url)