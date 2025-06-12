import requests
from bs4 import BeautifulSoup
import time
from typing import Dict, Any
from urllib.parse import urlparse
from ..exceptions.scraper_exceptions import (
    ScraperTimeoutError, ScraperHTTPError, ScraperNetworkError,
    ScraperContentError, ScraperUnexpectedError
)
from ..config.settings import WebScrapingConfig
from .document import ParsedDocument


class WebScraper:
    def __init__(self, config: 'WebScrapingConfig' = None):
        # Use a string literal for WebScrapingConfig type hint if it's defined later in the same file
        # or ensure it's imported correctly.
        self.config = config or WebScrapingConfig()
        self.session = requests.Session()
        self.session.headers.update(self.config.headers)
        # Assuming config has chunk_size defined or a default is set for iter_content

    def fetch_page(self, url: str, headers: Dict[str, str] = None,
                     timeout: int = None) -> ParsedDocument:
        """
        Fetch and parse a webpage, returning a ParsedDocument object.

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
            # Corrected: Update with provided headers, not itself
            request_headers.update(headers)

        last_exception: Optional[Exception] = None # Added type hint for clarity

        for attempt in range(self.config.max_retries):
            try:
                if attempt > 0:
                    time.sleep(self.config.delay_between_requests)

                response = self.session.get(
                    url,
                    headers=request_headers,
                    timeout=request_timeout,
                    allow_redirects=self.config.follow_redirects,
                    stream=True # Use stream for large files
                )
                response.raise_for_status() # Raises HTTPError for bad responses (4xx or 5xx)

                # --- Start of CRITICAL CHANGES for content handling ---
                downloaded_size = 0
                raw_content_bytes = b""
                chunk_size = getattr(self.config, 'chunk_size', 8192) # Get chunk_size from config or use default

                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk: # filter out keep-alive new chunks
                        raw_content_bytes += chunk
                        downloaded_size += len(chunk)
                        if downloaded_size > self.config.max_page_size:
                            raise ScraperContentError(f"Page too large: {downloaded_size} bytes, max allowed: {self.config.max_page_size} bytes")

                # Decode the bytes content to a string using the response's detected encoding, or utf-8 as fallback
                html_content_string = raw_content_bytes.decode(response.encoding or 'utf-8', errors='ignore')
                # --- End of CRITICAL CHANGES ---

                # Create a BeautifulSoup object from the decoded string content
                soup_obj = BeautifulSoup(html_content_string, 'html.parser')

                # Apply exclusion tags BEFORE creating the ParsedDocument,
                # as the document expects a final soup object.
                for tag_name in self.config.exclude_tags:
                    for tag in soup_obj.find_all(tag_name):
                        tag.decompose()

                # Prepare the response_info dictionary
                response_info = {
                    'status_code': response.status_code,
                    'headers': dict(response.headers),
                    'final_url': response.url,
                    'elapsed_time': response.elapsed.total_seconds(), # Changed from 'elapsed' for consistency
                    'encoding': response.encoding,
                    'content_length': len(raw_content_bytes) # Use raw_content_bytes length
                }

                # --- Corrected ParsedDocument instantiation ---
                return ParsedDocument(
                    url=url,
                    html_content=html_content_string, # Now defined!
                    soup=soup_obj,
                    response_info=response_info # Explicitly passed as keyword argument
                )
                # --- End corrected instantiation ---
            except requests.exceptions.Timeout as e:
                last_exception = ScraperTimeoutError(f"Request timed out after {request_timeout} seconds for {url}: {e}")
            except requests.exceptions.HTTPError as e:
                last_exception = ScraperHTTPError(f"HTTP error {response.status_code} for {url}: {e}")
        # --- CRITICAL CHANGE: Move ScraperContentError above RequestException ---
            except (ValueError, ScraperContentError) as e: # This MUST come BEFORE RequestException
                last_exception = ScraperContentError(f"Content processing error for {url}: {e}")
            except requests.exceptions.RequestException as e: # This is more general
                last_exception = ScraperNetworkError(f"Network error for {url}: {e}")
            except Exception as e:
                last_exception = ScraperUnexpectedError(f"An unexpected error occurred for {url}: {e}")

            if last_exception:
                raise last_exception
            else:
                raise ScraperUnexpectedError(f"Failed to fetch {url} after {self.config.max_retries} attempts with unknown error.")
        