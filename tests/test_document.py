import pytest
from bs4 import BeautifulSoup
import hashlib
from web_scraper.core.document import ParsedDocument
from web_scraper.core.models import ElementInfo, ElementType, ElementSignature
from collections import Counter # Need to import Counter for tests that verify its usage

# Fixture for a simple ParsedDocument
@pytest.fixture
def simple_html_doc():
    html = """
    <html>
        <head>
            <title>Test Page</title>
            <meta charset="utf-8">
        </head>
        <body>
            <div id="container">
                <p class="text">Hello</p>
                <p class="text">World</p>
                <a href="#">Link</a>
            </div>
            <span>Span text</span>
        </body>
    </html>
    """
    soup = BeautifulSoup(html, 'html.parser')
    response_info = {'status_code': 200, 'final_url': 'http://test.com', 'content_length': len(html)}
    doc = ParsedDocument('http://test.com', soup, response_info)
    doc.extract_all_elements() # <--- ADD THIS LINE
    return doc
    
def test_extract_all_elements(simple_html_doc):
    elements = simple_html_doc.extract_all_elements()
    assert len(elements) > 0 # Should extract more than 0 elements

    # Check for specific elements and their properties
    doc_elem = next((e for e in elements if e.tag == '[document]'), None)
    assert doc_elem is not None
    assert doc_elem.depth == 0
    assert doc_elem.children_count == 1 # html

    html_elem = next((e for e in elements if e.tag == 'html'), None)
    assert html_elem is not None
    assert html_elem.depth == 1
    assert html_elem.parent_signature == "[document]::no-id" # Simplified, depends on generate_signature_string output for doc
    assert html_elem.children_count == 2 # head, body

    p_elements = [e for e in elements if e.tag == 'p']
    assert len(p_elements) == 2
    assert p_elements[0].text == "Hello"
    assert p_elements[0].classes == ["text"]
    assert p_elements[0].depth == 4 # [document]/html/body/div/p
    assert p_elements[0].xpath == "/[document]/html/body/div/p[1]"


def test_get_document_stats(simple_html_doc):
    stats = simple_html_doc.get_document_stats()

    assert stats['total_elements'] == 11 # Adjust this based on exact count from simple_html_doc structure
    assert stats['unique_tags'] == 10 # Adjust based on exact tags in simple_html_doc
    assert stats['max_depth'] == 4 # Adjust based on max depth in simple_html_doc
    assert stats['avg_depth'] ==  2.6363636363636362 # Calculate and adjust expected average
    assert stats['elements_with_classes'] == 2 # 2 'p' tags with class="text"
    assert stats['elements_with_ids'] == 1 # 'div' with id="container"
    assert stats['elements_with_text'] == 10 # Count elements that have text

    assert 'meta' in stats['most_common_tags']
    assert 'p' in stats['most_common_tags']
    assert 'content' in stats['element_types']
    assert 'metadata' in stats['element_types']
    assert 'interactive' in stats['element_types']

def test_find_potential_patterns(simple_html_doc):
    patterns = simple_html_doc.find_potential_patterns(min_threshold=2)
    assert len(patterns) == 1 # Expecting 'meta' (2) and 'p' (2) tags

    # Verify the 'meta' pattern
    # meta_sig = next(s for s, elems in patterns.items() if s.tag == 'meta')
    # assert meta_sig is not None
    # assert len(patterns[meta_sig]) == 1 # Only one meta tag in the provided simple_html_doc HTML, but the original was 2, I need to fix the HTML above to be consistent for a true test
    # Let's adjust the simple_html_doc above to have two meta tags for a better test.
    # Re-evaluating the simple_html_doc. There's 1 meta tag. So this test expectation might be off.
    # Let's assume the HTML I provided initially (with 3 meta tags) was implicitly used for the output.
    # For this specific fixture, with ONE meta tag, min_threshold=2 means no meta pattern.
    # So, we expect only the 'p' tag pattern.
    # p_sig = next(s for s, elems in patterns.items() if s.tag == 'p')
    # Calculate the expected classes_hash for ['item']
    #expected_p_classes_hash = hashlib.md5("item".encode()).hexdigest()[:8]
    # For simple_html_doc, the 'p' tags have class="text"
    expected_p_classes_hash_for_text = hashlib.md5("text".encode()).hexdigest()[:8]
    p_sig = next(s for s, elems in patterns.items() if s.tag == 'p' and s.classes_hash == expected_p_classes_hash_for_text)
    assert p_sig is not None
    assert len(patterns[p_sig]) == 2
    assert patterns[p_sig][0].text == "Hello"
    assert patterns[p_sig][1].text == "World"


# Re-evaluate simple_html_doc elements and counts to make these tests accurate.
# Let's revise simple_html_doc to explicitly have two meta tags for a pattern test.
@pytest.fixture
def html_with_patterns_doc():
    html = """
    <html>
        <head>
            <title>Test Page</title>
            <meta name="keywords" content="test">
            <meta name="description" content="a test page">
        </head>
        <body>
            <div id="container">
                <p class="item">Item 1</p>
                <p class="item">Item 2</p>
                <p class="item">Item 3</p>
            </div>
            <button>Click 1</button>
            <button>Click 2</button>
        </body>
    </html>
    """
    soup = BeautifulSoup(html, 'html.parser')
    response_info = {'status_code': 200, 'final_url': 'http://pattern.com', 'content_length': len(html)}
    doc= ParsedDocument('http://pattern.com', soup, response_info)
    doc.extract_all_elements() # <--- ADD THIS LINE to populate _element_signatures
    return doc

def test_find_potential_patterns_with_multiple_types(html_with_patterns_doc):
    patterns = html_with_patterns_doc.find_potential_patterns(min_threshold=2)
    # Expected patterns: <meta> (2), <p class="item"> (3), <button> (2)
    assert len(patterns) == 3

    meta_sig = next(s for s, elems in patterns.items() if s.tag == 'meta')
    assert meta_sig is not None
    assert len(patterns[meta_sig]) == 2

    expected_p_item_classes_hash = hashlib.md5("item".encode()).hexdigest()[:8]
    p_item_sig = next(s for s, elems in patterns.items() if s.tag == 'p' and s.classes_hash == expected_p_item_classes_hash)
    assert p_item_sig is not None
    assert len(patterns[p_item_sig]) == 3

    button_sig = next(s for s, elems in patterns.items() if s.tag == 'button')
    assert button_sig is not None
    assert len(patterns[button_sig]) == 2