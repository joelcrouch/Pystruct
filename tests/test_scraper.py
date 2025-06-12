import pytest
import requests
from web_scraper.core.scraper import WebScraper
from web_scraper.config.settings import WebScrapingConfig
from web_scraper.core.document import ParsedDocument # To check return type
from web_scraper.exceptions.scraper_exceptions import (
    ScraperHTTPError, ScraperTimeoutError, ScraperContentError, ScraperNetworkError
)
# Define a fixture for a default scraper instance
@pytest.fixture
def default_scraper():
    return WebScraper(WebScrapingConfig(max_retries=1)) # Set retries to 1 for easier testing

def test_fetch_page_success(default_scraper, mocker):
    """Test successful page fetching."""
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.content = b"<html><body><h1>Test</h1></body></html>"
    mock_response.url = "http://example.com/test"
    mock_response.headers = {'Content-Type': 'text/html', 'Content-Length': '40'}
    mock_response.elapsed.total_seconds.return_value = 0.1 # Mock elapsed time
    mock_response.encoding = 'utf-8'
    mock_response.raise_for_status.return_value = None
    mock_response.iter_content.return_value = [b"<html><body><h1>Test</h1></body></html>"]

    mocker.patch('requests.Session.get', return_value=mock_response)

    doc = default_scraper.fetch_page("http://example.com")
    assert isinstance(doc, ParsedDocument)
    assert doc.url == "http://example.com"
    assert doc.response_info['status_code'] == 200
    assert "Test" in doc.soup.get_text()

def test_fetch_page_404_error(default_scraper, mocker):
    """Test fetching a page that returns a 404 error."""
    mock_response = mocker.Mock()
    mock_response.status_code = 404
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
    mock_response.iter_content.return_value = [b""] # Ensure content is iterated even on error
    # ADD THIS LINE: Mock the headers dictionary and its get method
    mock_response.headers = {'Content-Type': 'text/html'} # No 'Content-Length' for 404, or explicitly set to None/''
    # Or, to be super explicit:
    # mock_response.headers.get.return_value = None # This also works if headers is a Mock

    mocker.patch('requests.Session.get', return_value=mock_response)

    with pytest.raises(ScraperHTTPError): # Expect custom exception
        default_scraper.fetch_page("http://example.com/nonexistent")

def test_fetch_page_timeout(default_scraper, mocker):
    """Test fetching a page that times out."""
    mocker.patch('requests.Session.get', side_effect=requests.exceptions.Timeout("Timed out"))

    with pytest.raises(ScraperTimeoutError): # Expect custom exception
        default_scraper.fetch_page("http://example.com/slow")

def test_fetch_page_invalid_url(default_scraper):
    """Test fetching with an invalid URL."""
    with pytest.raises(ValueError, match="Invalid URL"):
        default_scraper.fetch_page("invalid-url")

def test_fetch_page_max_page_size_exceeded(default_scraper, mocker):
    """Test handling of pages exceeding max_page_size."""
    default_scraper.config.max_page_size = 50 # Set a small limit

    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.headers = {'Content-Type': 'text/html', 'Content-Length': '1000'} # Header larger than limit
    mock_response.iter_content.return_value = [b"a" * 60] # Simulate content coming in chunks, exceeding limit
    mock_response.url = "http://example.com/large"
    mock_response.elapsed.total_seconds.return_value = 0.1
    mock_response.encoding = 'utf-8'
    mock_response.raise_for_status.return_value = None


    mocker.patch('requests.Session.get', return_value=mock_response)

    with pytest.raises(ScraperContentError, match="Page too large"): # Expect custom exception
        default_scraper.fetch_page("http://example.com/large-page")

def test_fetch_page_excludes_tags(default_scraper, mocker):
    """Test that specified tags are excluded from the parsed content."""
    default_scraper.config.exclude_tags = ['script', 'style']

    mock_html = b"<html><body><script>alert('x');</script><p>Content</p><style>body{}</style></body></html>"
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.content = mock_html
    mock_response.url = "http://example.com"
    mock_response.headers = {'Content-Type': 'text/html', 'Content-Length': str(len(mock_html))}
    mock_response.elapsed.total_seconds.return_value = 0.1
    mock_response.encoding = 'utf-8'
    mock_response.raise_for_status.return_value = None
    mock_response.iter_content.return_value = [mock_html]


    mocker.patch('requests.Session.get', return_value=mock_response)

    doc = default_scraper.fetch_page("http://example.com")
    assert "<script>" not in str(doc.soup)
    assert "<style>" not in str(doc.soup)
    assert "<p>Content</p>" in str(doc.soup)