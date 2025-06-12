import requests

class WebScraperError(Exception):
    """Base exception for web scraper errors."""
    pass

class PageTooLargeError(WebScraperError):
    """Exception raised when a page exceeds the maximum allowed size."""
    def __init__(self, message="Page content too large", size_bytes=0, max_size_bytes=0):
        super().__init__(message)
        self.size_bytes = size_bytes
        self.max_size_bytes = max_size_bytes

class InvalidURLError(WebScraperError):
    """Exception raised when a provided URL is invalid."""
    def __init__(self, message="Invalid URL"):
        super().__init__(message)


class ScraperError(requests.RequestException):
    """Base exception for all scraper-related errors."""
    pass

class ScraperTimeoutError(ScraperError):
    """Exception raised when a request times out."""
    pass

class ScraperHTTPError(ScraperError):
    """Exception raised for HTTP errors (4xx or 5xx responses)."""
    pass

class ScraperNetworkError(ScraperError):
    """Exception raised for network-related issues (e.g., connection problems)."""
    pass

class ScraperContentError(ScraperError):
    """Exception raised for issues related to page content (e.g., page too large)."""
    pass

class ScraperUnexpectedError(ScraperError):
    """Exception raised for any other unexpected errors during scraping."""
    pass

# You
# 
# 
# can add more specific exceptions as needed in later sprints, e.g.,
# class PatternDetectionError(WebScraperError): pass
# class ExtractionError(WebScraperError): pass