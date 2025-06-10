from typing import List, Dict


class WebScrapingConfig:
    """Configuration class for web scraping behavior"""

    def __init__(self,
                 timeout: int = 30,
                 max_retries: int = 3,
                 delay_between_requests: float = 1.0,
                 user_agent: str = "WebScraperLibrary/1.0",
                 follow_redirects: bool = True,
                 max_page_size: int = 10 * 1024 * 1024,  # 10MB
                 exclude_tags: List[str] = None,
                 include_metadata: bool = False):

        self.timeout = timeout
        self.max_retries = max_retries
        self.delay_between_requests = delay_between_requests
        self.user_agent = user_agent
        self.follow_redirects = follow_redirects
        self.max_page_size = max_page_size
        self.exclude_tags = exclude_tags or ['script', 'style', 'noscript']
        self.include_metadata = include_metadata

        # Request headers
        self.headers = {
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }