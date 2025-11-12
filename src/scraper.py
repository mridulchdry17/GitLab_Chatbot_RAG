"""
GitLab Handbook and Direction Pages Scraper
Scrapes content with metadata: source_url, section_title, start_char, end_char
"""

import requests
from bs4 import BeautifulSoup
import json
import os
from typing import List, Dict
from urllib.parse import urljoin, urlparse
import time
import re


class GitLabScraper:
    """Scraper for GitLab Handbook and Direction pages with recursive link following"""
    
    BASE_URLS = {
        'handbook': 'https://handbook.gitlab.com',
        'direction': 'https://about.gitlab.com/direction'
    }
    
    def __init__(self, output_dir: str = 'data', max_depth: int = 3, max_pages: int = 100):
        self.output_dir = output_dir
        self.max_depth = max_depth  # Maximum depth for recursive crawling
        self.max_pages = max_pages  # Maximum total pages to scrape
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        os.makedirs(output_dir, exist_ok=True)
        self.visited_urls = set()  # Track visited URLs to avoid duplicates
        self.scraped_count = 0  # Track total pages scraped
        
    def clean_text(self, text: str) -> str:
        """Clean and normalize text content"""
        if not text:
            return ""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove leading/trailing whitespace
        text = text.strip()
        return text
    
    def extract_sections(self, soup: BeautifulSoup, url: str) -> List[Dict]:
        """
        Extract content sections with metadata
        Returns chunks with: source_url, section_title, start_char, end_char, content
        """
        chunks = []
        content_text = ""
        
        # Find main content area (adjust selectors based on GitLab's structure)
        main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=re.compile('content|main|article'))
        
        if not main_content:
            main_content = soup.find('body')
        
        # Extract all headings and content
        current_section_title = "Introduction"
        current_section_content = []
        char_offset = 0
        
        for element in main_content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'li', 'div']):
            # Skip navigation, footer, header elements
            if element.find_parent(['nav', 'header', 'footer', 'aside']):
                continue
                
            text = self.clean_text(element.get_text())
            if not text or len(text) < 10:
                continue
            
            # If it's a heading, save previous section and start new one
            if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                # Save previous section if it has content
                if current_section_content:
                    section_text = ' '.join(current_section_content)
                    if len(section_text) > 50:  # Minimum chunk size
                        start_char = char_offset
                        end_char = char_offset + len(section_text)
                        
                        chunks.append({
                            'source_url': url,
                            'section_title': current_section_title,
                            'start_char': start_char,
                            'end_char': end_char,
                            'content': section_text
                        })
                        char_offset = end_char
                
                # Start new section
                current_section_title = text
                current_section_content = []
            else:
                # Add to current section
                current_section_content.append(text)
        
        # Save last section
        if current_section_content:
            section_text = ' '.join(current_section_content)
            if len(section_text) > 50:
                start_char = char_offset
                end_char = char_offset + len(section_text)
                
                chunks.append({
                    'source_url': url,
                    'section_title': current_section_title,
                    'start_char': start_char,
                    'end_char': end_char,
                    'content': section_text
                })
        
        # If no sections found, create one chunk from all content
        if not chunks:
            all_text = self.clean_text(main_content.get_text())
            if len(all_text) > 50:
                chunks.append({
                    'source_url': url,
                    'section_title': "Main Content",
                    'start_char': 0,
                    'end_char': len(all_text),
                    'content': all_text
                })
        
        return chunks
    
    def scrape_page(self, url: str) -> List[Dict]:
        """Scrape a single page and return chunks with metadata"""
        try:
            print(f"Scraping: {url}")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            # Try lxml first, fallback to html.parser if not available
            try:
                soup = BeautifulSoup(response.content, 'lxml')
            except:
                soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "header", "footer"]):
                script.decompose()
            
            chunks = self.extract_sections(soup, url)
            print(f"  Extracted {len(chunks)} chunks")
            
            return chunks
            
        except Exception as e:
            print(f"Error scraping {url}: {str(e)}")
            return []
    
    def is_valid_url(self, url: str, base_domain: str) -> bool:
        """Check if URL is valid for scraping"""
        try:
            parsed = urlparse(url)
            # Must be from the same domain
            if base_domain == 'handbook':
                if 'handbook.gitlab.com' not in parsed.netloc and parsed.netloc != '':
                    return False
            elif base_domain == 'direction':
                if 'about.gitlab.com' not in parsed.netloc and parsed.netloc != '':
                    return False
                if '/direction' not in parsed.path:
                    return False
            
            # Skip common non-content URLs
            skip_patterns = [
                '/search', '/login', '/logout', '/sign', '/api/', 
                '.pdf', '.zip', '.jpg', '.png', '.gif', '.svg',
                '#', 'mailto:', 'tel:', 'javascript:'
            ]
            for pattern in skip_patterns:
                if pattern in url.lower():
                    return False
            
            # Must be HTTP/HTTPS
            if not url.startswith(('http://', 'https://')):
                return False
            
            return True
        except:
            return False
    
    def extract_links(self, soup: BeautifulSoup, current_url: str, base_domain: str) -> List[str]:
        """Extract all valid links from a page"""
        links = []
        base_url = self.BASE_URLS[base_domain]
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            
            # Convert relative URLs to absolute
            if href.startswith('/'):
                full_url = urljoin(base_url, href)
            elif href.startswith(('http://', 'https://')):
                full_url = href
            else:
                full_url = urljoin(current_url, href)
            
            # Normalize URL (remove fragments, trailing slashes)
            full_url = full_url.split('#')[0].rstrip('/')
            
            # Validate URL
            if self.is_valid_url(full_url, base_domain):
                if full_url not in self.visited_urls:
                    links.append(full_url)
        
        return links
    
    def crawl_recursive(self, start_urls: List[str], base_domain: str, depth: int = 0) -> List[str]:
        """
        Recursively crawl pages starting from start_urls
        Returns list of all URLs to scrape
        """
        if depth > self.max_depth or len(self.visited_urls) >= self.max_pages:
            return []
        
        urls_to_scrape = []
        next_level_urls = []
        
        for url in start_urls:
            if url in self.visited_urls:
                continue
            
            if len(self.visited_urls) >= self.max_pages:
                break
            
            try:
                print(f"  [Depth {depth}] Discovering links from: {url}")
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                
                # Try lxml first, fallback to html.parser if not available
                try:
                    soup = BeautifulSoup(response.content, 'lxml')
                except:
                    soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract links from this page
                found_links = self.extract_links(soup, url, base_domain)
                
                # Mark as visited (for discovery phase)
                self.visited_urls.add(url)
                urls_to_scrape.append(url)
                
                # Add new links for next level
                for link in found_links:
                    if link not in self.visited_urls and link not in next_level_urls:
                        next_level_urls.append(link)
                
                time.sleep(0.5)  # Rate limiting
                
            except Exception as e:
                print(f"  Error discovering links from {url}: {str(e)}")
                continue
        
        # Recursively crawl next level
        if next_level_urls and depth < self.max_depth and len(self.visited_urls) < self.max_pages:
            deeper_urls = self.crawl_recursive(next_level_urls, base_domain, depth + 1)
            urls_to_scrape.extend(deeper_urls)
        
        return urls_to_scrape
    
    def find_all_pages(self, base_domain: str = 'handbook') -> List[str]:
        """
        Find all pages to scrape by recursively following links
        base_domain: 'handbook' or 'direction'
        """
        print(f"\n{'='*60}")
        print(f"Discovering {base_domain} pages (max depth: {self.max_depth}, max pages: {self.max_pages})")
        print(f"{'='*60}")
        
        # Reset tracking for this domain
        self.visited_urls = set()
        self.scraped_count = 0
        
        # Start with base URL
        start_url = self.BASE_URLS[base_domain]
        all_urls = self.crawl_recursive([start_url], base_domain, depth=0)
        
        print(f"\nDiscovered {len(all_urls)} unique pages to scrape")
        return all_urls
    
    def scrape_all(self):
        """Scrape all handbook and direction pages recursively"""
        all_chunks = []
        
        # Discover and scrape handbook pages
        print("\n" + "=" * 60)
        print("PHASE 1: Discovering Handbook Pages")
        print("=" * 60)
        handbook_urls = self.find_all_pages('handbook')
        
        print("\n" + "=" * 60)
        print("PHASE 2: Scraping Handbook Content")
        print("=" * 60)
        for i, url in enumerate(handbook_urls, 1):
            print(f"[{i}/{len(handbook_urls)}] ", end="")
            chunks = self.scrape_page(url)
            all_chunks.extend(chunks)
            time.sleep(0.8)  # Be respectful with rate limiting
        
        # Discover and scrape direction pages
        print("\n" + "=" * 60)
        print("PHASE 3: Discovering Direction Pages")
        print("=" * 60)
        direction_urls = self.find_all_pages('direction')
        
        print("\n" + "=" * 60)
        print("PHASE 4: Scraping Direction Content")
        print("=" * 60)
        for i, url in enumerate(direction_urls, 1):
            print(f"[{i}/{len(direction_urls)}] ", end="")
            chunks = self.scrape_page(url)
            all_chunks.extend(chunks)
            time.sleep(0.8)
        
        # Save all chunks
        output_file = os.path.join(self.output_dir, 'gitlab_chunks.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_chunks, f, indent=2, ensure_ascii=False)
        
        print(f"\n{'=' * 60}")
        print(f"✅ Scraping complete!")
        print(f"   Total pages scraped: {len(handbook_urls) + len(direction_urls)}")
        print(f"   Total chunks extracted: {len(all_chunks)}")
        print(f"   Saved to: {output_file}")
        print(f"{'=' * 60}")
        
        return all_chunks


if __name__ == '__main__':
    # Configure scraper
    # max_depth: How many levels deep to follow links (default: 3)
    # max_pages: Maximum total pages to scrape per domain (default: 100)
    scraper = GitLabScraper(max_depth=3, max_pages=100)
    
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║  GitLab Handbook & Direction Scraper                        ║
    ║  Recursive Link Following Enabled                            ║
    ╚══════════════════════════════════════════════════════════════╝
    
    This scraper will:
    1. Start from the base Handbook/Direction URLs
    2. Recursively follow ALL links found on each page
    3. Scrape content from discovered pages
    4. Track metadata: source_url, section_title, start_char, end_char
    
    Configuration:
    - Max Depth: {} levels
    - Max Pages per Domain: {}
    
    Note: This may take a while depending on the number of pages.
    """.format(scraper.max_depth, scraper.max_pages))
    
    scraper.scrape_all()

