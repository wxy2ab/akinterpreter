import requests
from bs4 import BeautifulSoup, Comment

class UrlReader:
    def __init__(self, url):
        self.url = url
        self.cleaned_html = ""
        self.text_content = ""
        self._fetch_and_clean()

    def _fetch_and_clean(self):
        response = requests.get(self.url)
        soup = BeautifulSoup(response.content, 'html.parser')

        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        # Remove comments
        for comment in soup.find_all(text=lambda text: isinstance(text, Comment)):
            comment.extract()

        # Remove specific tags that are likely to contain boilerplate content
        for tag in soup(['header', 'nav', 'footer', 'aside']):
            tag.decompose()

        self.cleaned_html = str(soup)
        self.text_content = soup.get_text(separator='\n', strip=True)

    def get_cleaned_html(self):
        return self.cleaned_html

    def get_text_content(self):
        return self.text_content