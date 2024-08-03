import requests
from bs4 import BeautifulSoup
import json
import time
import logging

from ..utils.log import logger

def get_content(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        logger.error(f"Error fetching {url}: {e}")
        return None

def parse_menu(soup):
    menu_items = []
    menu = soup.select_one('#jstree')
    if menu:
        for item in menu.find_all('a'):
            name = item.text.strip()
            href = item.get('href')
            if href and name:
                menu_items.append({'name': name, 'href': href})
    return menu_items

def parse_content(soup):
    content_div = soup.select_one('.content')
    if content_div:
        # Remove the search panel and footer if present
        for element in content_div.select('.search-panel, footer'):
            element.extract()
        
        # Get all content after h1 or h2
        start_tag = content_div.find(['h1', 'h2'])
        if start_tag:
            content = ''.join(str(tag) for tag in start_tag.next_siblings)
            return content.strip()
    return ''

def scrape_tushare_docs():
    base_url = 'https://tushare.pro'
    start_url = f'{base_url}/document/2'
    
    result = []
    visited = set()

    def scrape_page(url):
        if url in visited:
            return
        visited.add(url)

        logger.info(f"Scraping: {url}")
        html = get_content(url)
        if html is None:
            return

        soup = BeautifulSoup(html, 'html.parser')
        
        menu_items = parse_menu(soup)
        content = parse_content(soup)

        result.append({
            'name': soup.select_one('h1, h2').text if soup.select_one('h1, h2') else '',
            'href': url.replace(base_url, ''),
            'content': content
        })

        for item in menu_items:
            full_url = base_url + item['href']
            if full_url not in visited:
                scrape_page(full_url)

        time.sleep(1)  # Be polite to the server

    scrape_page(start_url)
    return result

def save_to_json(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    docs = scrape_tushare_docs()
    save_to_json(docs, './json/tushare_doc_full.json')
    logger.info("Scraping completed. Results saved to ./json/tushare_doc_full.json")