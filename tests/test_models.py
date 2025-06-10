import hashlib
from web_scraper.core.models import ElementInfo, ElementSignature, ElementType

def test_element_info_creation():
    """Test basic ElementInfo creation and post_init behavior."""
    element = ElementInfo(
        tag="div",
        classes=["class1", " class2 "],
        id="my-id",
        text="  Some   text here  ",
        attributes={"data-test": "value"},
        depth=2,
        xpath="/html/body/div"
    )
    assert element.tag == "div"
    assert element.classes == ["class1", "class2"] # Check for stripping
    assert element.id == "my-id"
    assert element.text == "Some text here"       # Check for stripping and single spaces
    assert element.attributes == {"data-test": "value"}
    assert element.depth == 2
    assert element.xpath == "/html/body/div"
    assert element.element_type == ElementType.CONTENT # Default type
    assert element.children_count == 0

def test_element_signature_hashing_and_equality():
    """Test ElementSignature's hash and equality methods."""
    sig1 = ElementSignature(
        tag="div",
        classes_hash=hashlib.md5("class1,class2".encode()).hexdigest()[:8],
        id_present=True,
        parent_context="body:",
        depth_range="2-4"
    )
    sig2 = ElementSignature(
        tag="div",
        classes_hash=hashlib.md5("class1,class2".encode()).hexdigest()[:8],
        id_present=True,
        parent_context="body:",
        depth_range="2-4"
    )
    sig3 = ElementSignature(
        tag="p", # Different tag
        classes_hash=hashlib.md5("class1,class2".encode()).hexdigest()[:8],
        id_present=True,
        parent_context="body:",
        depth_range="2-4"
    )

    assert sig1 == sig2
    assert hash(sig1) == hash(sig2)
    assert sig1 != sig3
    assert hash(sig1) != hash(sig3) # Not guaranteed to be different, but highly likely