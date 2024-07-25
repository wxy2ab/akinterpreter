import asyncio
import re
import aiohttp
import logging
from bs4 import BeautifulSoup, Comment, NavigableString, Tag
from playwright.async_api import async_playwright
from tenacity import retry, stop_after_attempt, wait_exponential

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UrlReader:
    def __init__(self):
        self.url = None
        self.cleaned_html = ""
        self.text_content = ""

    async def read_url(self, url, wait_for_selector=None, timeout=30000):
        self.url = url
        content = None

        methods = [
            self._fetch_with_playwright,
            self._fetch_with_aiohttp,
        ]

        for method in methods:
            try:
                content = await method(url, wait_for_selector, timeout)
                if self._is_content_complete(content):
                    break
            except Exception as e:
                logger.error(f"Error with {method.__name__}: {str(e)}", exc_info=True)

        self._clean_content(content)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def _fetch_with_playwright(self, url, wait_for_selector=None, timeout=30000):
        async with async_playwright() as p:
            browser = await p.chromium.launch(args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage'])
            try:
                page = await browser.new_page()
                await page.goto(url, wait_until='networkidle', timeout=timeout)

                if wait_for_selector:
                    await page.wait_for_selector(wait_for_selector, timeout=timeout)

                content = await page.content()
                return content
            except Exception as e:
                logger.error(f"Playwright error: {str(e)}", exc_info=True)
                raise
            finally:
                await browser.close()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def _fetch_with_aiohttp(self, url, wait_for_selector=None, timeout=30000):
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=timeout/1000) as response:
                return await response.text()

    def _is_content_complete(self, content):
        return content and len(content) > 1000 and '<body' in content and '</body>' in content

    def _clean_content(self, content):
        if not content:
            self.cleaned_html = ""
            self.text_content = ""
            return

        soup = BeautifulSoup(content, 'html.parser')

        # 移除所有HTML注释
        for comment in soup.find_all(text=lambda text: isinstance(text, Comment)):
            comment.extract()

        # 移除所有脚本、样式和元数据元素
        for element in soup(["script", "style", "meta", "link", "noscript"]):
            element.decompose()

        # 移除所有属性
        for tag in soup.find_all(True):
            tag.attrs = {}

        # 简化HTML结构
        def simplify_structure(element):
            if isinstance(element, NavigableString):
                return element if element.strip() else None
            
            new_children = []
            for child in element.children:
                if isinstance(child, Tag):
                    if child.name in ['div', 'span']:
                        child.name = 'p'
                    simplified_child = simplify_structure(child)
                    if simplified_child:
                        new_children.append(simplified_child)
                elif isinstance(child, NavigableString) and child.strip():
                    new_children.append(child)
            
            if not new_children:
                return None
            
            element.clear()
            for child in new_children:
                element.append(child)
            
            return element

        simplify_structure(soup)

        # 移除空的标签
        for element in soup.find_all(lambda tag: len(tag.get_text(strip=True)) == 0):
            element.decompose()

        # 合并连续的p标签
        for p in soup.find_all('p'):
            next_siblings = list(p.next_siblings)
            for sibling in next_siblings:
                if sibling.name == 'p':
                    p.append(' ')
                    p.extend(sibling.contents)
                    sibling.decompose()
                else:
                    break

        # 重新构建清理后的HTML
        html = str(soup)
        
        # 移除多余的空行
        html = re.sub(r'\n\s*\n', '\n', html)
        
        # 移除p标签内的多余空格
        html = re.sub(r'<p>\s+', '<p>', html)
        html = re.sub(r'\s+</p>', '</p>', html)
        
        self.cleaned_html = html

        # 提取文本内容
        self.text_content = soup.get_text(separator='\n', strip=True)
        
        # 移除文本内容中的多余空行
        self.text_content = re.sub(r'\n\s*\n', '\n', self.text_content)

    def get_cleaned_html(self):
        return self.cleaned_html

    def get_text_content(self):
        return self.text_content

# Helper function to run the async method
async def read_url_async(url, wait_for_selector=None, timeout=30000):
    reader = UrlReader()
    await reader.read_url(url, wait_for_selector, timeout)
    return reader

# Synchronous wrapper for backwards compatibility
def read_url_sync(url, wait_for_selector=None, timeout=30000):
    return asyncio.get_event_loop().run_until_complete(read_url_async(url, wait_for_selector, timeout))