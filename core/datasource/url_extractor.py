


from .url_js_reader import UrlReader
from ._file_reader import FileReader


class UrlExtractor(FileReader):
    def __init__(self, url, wait_for_selector=None, timeout=30000):
        super().__init__(url)
        self.url_reader = UrlReader()
        self.wait_for_selector = wait_for_selector
        self.timeout = timeout

    async def read_file(self):
        await self.url_reader.read_url(self.file_path, self.wait_for_selector, self.timeout)
        self.content = [
            {"type": "html", "content": self.url_reader.get_cleaned_html()},
            {"type": "text", "content": self.url_reader.get_text_content()},
        ]
        self.summary = self.generate_summary()

    def generate_summary(self):
        text_length = len(self.url_reader.get_text_content())
        summary = f"URL: {self.file_path}\n"
        summary += f"纯文本长度: {text_length}\n"
        return summary