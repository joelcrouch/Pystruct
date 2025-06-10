from web_scraper.config.settings import WebScrapingConfig

def test_web_scraping_config_defaults():
    """Test default values of WebScrapingConfig."""
    config = WebScrapingConfig()
    assert config.timeout == 30
    assert config.max_retries == 3
    assert config.delay_between_requests == 1.0
    assert config.headers['User-Agent'] == "WebScraperLibrary/1.0"
    assert config.follow_redirects is True
    assert config.max_page_size == 10 * 1024 * 1024
    assert config.exclude_tags == ['script', 'style', 'noscript']
    assert config.include_metadata is False
    assert 'User-Agent' in config.headers
    assert config.user_agent == "WebScraperLibrary/1.0"

def test_web_scraping_config_custom_values():
    """Test setting custom values for WebScrapingConfig."""
    config = WebScrapingConfig(
        timeout=5,
        max_retries=5,
        user_agent="MyCustomBot/1.0",
        exclude_tags=['img'],
        include_metadata=True
    )
    assert config.timeout == 5
    assert config.max_retries == 5
    assert config.user_agent == "MyCustomBot/1.0"
    assert config.exclude_tags == ['img']
    assert config.include_metadata is True
    assert config.headers['User-Agent'] == "MyCustomBot/1.0"