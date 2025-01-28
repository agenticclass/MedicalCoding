import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
from urllib.parse import urljoin, urlparse
import re

def create_output_directory():
    output_dir = os.path.join(os.path.dirname(__file__), 'akasa')
    os.makedirs(output_dir, exist_ok=True)
    return output_dir

def is_valid_url(url):
    """Check if URL belongs to akasa.com domain"""
    parsed = urlparse(url)
    return parsed.netloc.endswith('akasa.com')

def clean_filename(url):
    """Convert URL to a valid filename"""
    # Remove protocol and domain
    filename = re.sub(r'https?://[^/]+/', '', url)
    # Replace special characters
    filename = re.sub(r'[^a-zA-Z0-9]', '_', filename)
    # Handle empty or root path
    return filename if filename else 'index'

def get_page_content(url, session):
    """Fetch and extract content from a single page"""
    try:
        response = session.get(url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'footer', 'header']):
            element.decompose()
            
        # Get text content
        text = soup.get_text()
        
        # Clean up text
        lines = (line.strip() for line in text.splitlines())
        text = '\n'.join(line for line in lines if line)
        
        # Extract links
        links = []
        for a in soup.find_all('a', href=True):
            href = urljoin(url, a['href'])
            if is_valid_url(href):
                links.append(href)
                
        return text, links
        
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None, []

def save_text(text, url, output_dir):
    """Save text content to a file"""
    if text:
        filename = f"{clean_filename(url)}.txt"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"URL: {url}\n\n")
            f.write(text)
        print(f"Saved content from: {url}")
    else:
        print(f"No content to save for: {url}")

def scrape_website(start_url='https://akasa.com/'):
    """Scrape entire website starting from the given URL"""
    session = requests.Session()
    visited_urls = set()
    urls_to_visit = {start_url}
    
    while urls_to_visit:
        url = urls_to_visit.pop()
        if url in visited_urls:
            continue
            
        print(f"Scraping: {url}")
        content, links = get_page_content(url, session)
        
        if content:
            yield url, content
            
        visited_urls.add(url)
        # Add new links to visit
        urls_to_visit.update(link for link in links if link not in visited_urls)
        
        # Respect the website by waiting between requests
        time.sleep(1)

def main():
    print("Starting web scraping...")
    output_dir = create_output_directory()
    
    for url, content in scrape_website():
        save_text(content, url, output_dir)
    
    print("Scraping completed!")

if __name__ == '__main__':
    main()
