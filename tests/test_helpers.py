from bs4 import BeautifulSoup, Tag
from web_scraper.utils.helpers import generate_xpath, classify_element, \
    generate_element_signature, generate_signature_string
from web_scraper.core.models import ElementInfo, ElementType, ElementSignature
import hashlib

def create_bs_tag(html_string: str, tag_name: str) -> Tag:
    """Helper to create a BeautifulSoup Tag from an HTML string."""
    soup = BeautifulSoup(html_string, 'html.parser')
    return soup.find(tag_name)

def test_generate_xpath_simple():
    html = "<html><body><div id='content'><p>Text</p></div></body></html>"
    soup = BeautifulSoup(html, 'html.parser')
    p_tag = soup.find('p')
    assert generate_xpath(p_tag) == "/[document]/html/body/div/p"

def test_generate_xpath_with_siblings():
    html = "<div><span>1</span><span>2</span></div>"
    soup = BeautifulSoup(html, 'html.parser')
    spans = soup.find_all('span')
    assert generate_xpath(spans[0]) == "/[document]/div/span[1]"
    assert generate_xpath(spans[1]) == "/[document]/div/span[2]"

def test_generate_xpath_root():
    html = "<html></html>"
    soup = BeautifulSoup(html, 'html.parser')
    html_tag = soup.find('html')
    assert generate_xpath(html_tag) == "/[document]/html"

def test_classify_element():
    assert classify_element("nav", [], {}) == ElementType.NAVIGATION
    assert classify_element("a", [], {}) == ElementType.INTERACTIVE
    assert classify_element("script", [], {}) == ElementType.METADATA
    assert classify_element("header", [], {}) == ElementType.STRUCTURAL
    assert classify_element("span", [], {}) == ElementType.CONTENT
    assert classify_element("div", ["navbar"], {}) == ElementType.NAVIGATION # Based on class

def test_generate_element_signature():
    element_info = ElementInfo(
        tag="div",
        classes=["product", "item"],
        id="prod123",
        parent_signature="body:main:no-id",
        depth=5
    )
    signature = generate_element_signature(element_info, include_parent=True, depth=2)
    classes_hash = hashlib.md5("item,product".encode()).hexdigest()[:8]
    assert signature.tag == "div"
    assert signature.classes_hash == classes_hash
    assert signature.id_present is True
    assert signature.parent_context == "body:main" # Sliced parent context
    assert signature.depth_range == "1-3"

def test_generate_signature_string():
    element_info = ElementInfo(
        tag="span",
        classes=["info", "highlight"],
        id="span-id"
    )
    assert generate_signature_string(element_info) == "span:highlight,info:span-id"

    element_info_no_id = ElementInfo(
        tag="p",
        classes=["text-block"]
    )
    assert generate_signature_string(element_info_no_id) == "p:text-block:no-id"