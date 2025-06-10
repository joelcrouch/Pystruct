import requests
from bs4 import BeautifulSoup
import time
from typing import Dict, Any
from urllib.parse import urlparse

from ..config.settings import WebScrapingConfig
from .document import ParsedDocument
# from ..exceptions.scraper_exceptions import CustomScraperError # To be implemented later


class WebScraper:
    """Main web scraper class implementing Sprint 1 functionality"""

    def __init__(self, config: WebScrapingConfig = None):
        self.config = config or WebScrapingConfig()
        self.session = requests.Session()
        self.session.headers.update(self.config.headers)

    def fetch_page(self, url: str, headers: Dict[str, str] = None,
                   timeout: int = None) -> ParsedDocument:
        """
        Fetch and parse a webpage, returning a ParsedDocument object

        Args:
            url: Target URL to scrape
            headers: Optional additional headers
            timeout: Optional timeout override

        Returns:
            ParsedDocument: Parsed document ready for analysis

        Raises:
            requests.RequestException: If fetching fails
            ValueError: If URL is invalid or response is too large
        """
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise ValueError(f"Invalid URL: {url}")

        request_timeout = timeout or self.config.timeout
        request_headers = self.config.headers.copy()
        if headers:
            request_headers.update(headers)

        last_exception = None
        for attempt in range(self.config.max_retries):
            try:
                if attempt > 0:
                    time.sleep(self.config.delay_between_requests)

                response = self.session.get(
                    url,
                    headers=request_headers,
                    timeout=request_timeout,
                    allow_redirects=self.config.follow_redirects,
                    stream=True
                )

                content_length = response.headers.get('content-length')
                if content_length and int(content_length) > self.config.max_page_size:
                    raise ValueError(f"Page too large: {content_length} bytes")

                content = b""
                for chunk in response.iter_content(chunk_size=8192):
                    content += chunk
                    if len(content) > self.config.max_page_size:
                        raise ValueError(f"Page too large: {len(content)} bytes")

                response._content = content
                response.raise_for_status()

                soup = BeautifulSoup(response.content, 'html.parser')

                for tag_name in self.config.exclude_tags:
                    for tag in soup.find_all(tag_name):
                        tag.decompose()

                response_info = {
                    'status_code': response.status_code,
                    'headers': dict(response.headers),
                    'final_url': response.url,
                    'elapsed': response.elapsed.total_seconds(),
                    'encoding': response.encoding,
                    'content_length': len(content)
                }

                return ParsedDocument(url, soup, response_info)

            except requests.RequestException as e:
                last_exception = e
                if attempt == self.config.max_retries - 1:
                    raise
                continue

        raise last_exception or requests.RequestException("Unknown error occurred")

    def get_session_info(self) -> Dict[str, Any]:
        """Get information about the current scraping session"""
        return {
            'config': {
                'timeout': self.config.timeout,
                'max_retries': self.config.max_retries,
                'user_agent': self.config.user_agent,
                'exclude_tags': self.config.exclude_tags
            },
            'session_headers': dict(self.session.headers)
        }