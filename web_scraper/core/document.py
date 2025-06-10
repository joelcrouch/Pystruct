from typing import List, Dict, Any
from bs4 import BeautifulSoup, Tag
import hashlib
from collections import Counter

from .models import ElementInfo, ElementSignature, ElementType
from ..utils.helpers import generate_xpath, classify_element, generate_element_signature


class ParsedDocument:
    """Main document representation with analysis capabilities"""

    def __init__(self, url: str, soup: BeautifulSoup, response_info: Dict[str, Any]):
        self.url = url
        self.soup = soup
        self.response_info = response_info
        self.elements: List[ElementInfo] = []
        self._element_signatures: Dict[ElementSignature, List[ElementInfo]] = {}
        self._analyzed = False

    def extract_all_elements(self) -> List[ElementInfo]:
        """Extract all HTML elements with their properties and relationships"""
        if self._analyzed:
            return self.elements

        self.elements = []
        self._extract_recursive(self.soup, depth=0, parent_sig="")
        self._analyzed = True
        return self.elements

    def _extract_recursive(self, element, depth: int = 0, parent_sig: str = ""):
        """Recursively extract elements and build the element tree"""
        if not isinstance(element, Tag):
            return

        # Create ElementInfo for current element
        element_info = self._create_element_info(element, depth, parent_sig)
        self.elements.append(element_info)

        # Get signature for this element to pass to children
        current_sig = self._generate_signature_string(element_info)

        # Process children
        children = [child for child in element.children if isinstance(child, Tag)]
        element_info.children_count = len(children)

        for child in children:
            self._extract_recursive(child, depth + 1, current_sig)

    def _create_element_info(self, element: Tag, depth: int, parent_sig: str) -> ElementInfo:
        """Create ElementInfo object from BeautifulSoup Tag"""
        tag = element.name.lower()
        classes = element.get('class', [])
        element_id = element.get('id')

        text_content = ""
        if element.string:
            text_content = element.string.strip()
        elif element.get_text():
            text_content = element.get_text(strip=True)[:200]

        attributes = {k: v for k, v in element.attrs.items()
                     if k not in ['class', 'id']}

        xpath = generate_xpath(element)
        element_type = classify_element(tag, classes, attributes)

        return ElementInfo(
            tag=tag,
            classes=classes,
            id=element_id,
            text=text_content,
            attributes=attributes,
            parent_signature=parent_sig,
            depth=depth,
            xpath=xpath,
            element_type=element_type
        )

    def _generate_signature_string(self, element_info: ElementInfo) -> str:
        """Generate a string representation of element signature for parent_signature field"""
        classes_str = ",".join(sorted(element_info.classes))
        return f"{element_info.tag}:{classes_str}:{element_info.id or 'no-id'}"

    def generate_signature(self, element_info: ElementInfo,
                          include_parent: bool = True, depth: int = 2) -> ElementSignature:
        """Generate a hashable signature for element grouping using helper."""
        return generate_element_signature(element_info, include_parent, depth)


    def get_elements_by_signature(self, signature: ElementSignature) -> List[ElementInfo]:
        """Get all elements matching a specific signature"""
        if not self._element_signatures:
            self._build_signature_index()

        return self._element_signatures.get(signature, [])

    def _build_signature_index(self):
        """Build index of elements by signature for fast lookup"""
        self._element_signatures.clear()

        for element in self.elements:
            signature = self.generate_signature(element)
            if signature not in self._element_signatures:
                self._element_signatures[signature] = []
            self._element_signatures[signature].append(element)

    def get_document_stats(self) -> Dict[str, Any]:
        """Get basic statistics about the document"""
        if not self._analyzed:
            self.extract_all_elements()

        tag_counts = Counter(el.tag for el in self.elements)
        type_counts = Counter(el.element_type.value for el in self.elements)

        # Calculate average depth
        total_depth = sum(el.depth for el in self.elements)
        avg_depth = total_depth / len(self.elements) if self.elements else 0

        # Return the complete dictionary with all expected keys
        return {
            'total_elements': len(self.elements),
            'unique_tags': len(set(el.tag for el in self.elements)),
            'max_depth': max((el.depth for el in self.elements), default=0),
            'avg_depth': avg_depth, # <--- ADD THIS LINE
            'elements_with_classes': sum(1 for el in self.elements if el.classes),
            'elements_with_ids': sum(1 for el in self.elements if el.id),
            'elements_with_text': sum(1 for el in self.elements if el.text),
            'most_common_tags': dict(tag_counts.most_common(10)), # <--- ADD THIS LINE
            'element_types': dict(type_counts), # <--- ADD THIS LINE
            # 'tag_distribution' was in your original snippet, but 'most_common_tags' is more specific for a dict.
            # I'd recommend using 'most_common_tags' as implemented here.
            # If you want both, just keep 'tag_distribution' too and fill it.
        }
        
    def find_potential_patterns(self, min_threshold: int = 2) -> Dict[ElementSignature, List[ElementInfo]]:
        """
        Find elements that appear multiple times (a preview for Sprint 2 functionality).
        Groups elements by their ElementSignature and returns groups meeting a min_threshold.
        """
        if not self._element_signatures:
            self._build_signature_index()

        patterns = {}
        for signature, elements in self._element_signatures.items():
            if len(elements) >= min_threshold:
                patterns[signature] = elements

        return patterns