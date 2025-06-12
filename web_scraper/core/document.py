from typing import List, Dict, Optional, Any, Tuple
from bs4 import BeautifulSoup, Tag, NavigableString
from dataclasses import dataclass, field
import hashlib
import time
from collections import Counter, defaultdict
from urllib.parse import urljoin, urlparse
from .models import ElementInfo, ElementSignature, ElementType, PatternInfo
from ..utils.helpers import generate_xpath, classify_element, generate_element_signature


class ParsedDocument:
    """Main document representation with analysis capabilities"""

    def __init__(self, url: str, html_content: str, soup: BeautifulSoup, response_info: Dict[str, Any]):
        self.url = url
        self.html_content = html_content # <--- CORRECTED: Assign as instance attribute
        self.soup = soup
        self.response_info = response_info
        self.elements: List[ElementInfo] = []
        self._element_signatures: Dict[ElementSignature, List[ElementInfo]] = {}
        self._analyzed = False # Flag to indicate if elements have been extracted

    def extract_all_elements(self) -> List[ElementInfo]:
        """Extract all HTML elements with their properties and relationships"""
        if self._analyzed:
            return self.elements

        self.elements = []
        # Iterate through the direct children of the BeautifulSoup object that are actual HTML Tags.
        # This correctly initiates the recursion with proper HTML elements.
        for child_element in self.soup.children:
            if isinstance(child_element, Tag):
                # Start recursion from depth 0 for these top-level HTML tags (e.g., <html>)
                self._extract_recursive(child_element, depth=0, parent_sig="")

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
    # """
    # Create ElementInfo object from BeautifulSoup Tag
    # """
        tag = element.name.lower()

        # --- START OF ROBUST FIX FOR CLASSES TYPE ---
        raw_classes_attr_value = element.get('class') # Get the 'class' attribute value, can be str, list[str], or None
        classes: List[str] # Declare the type of 'classes' explicitly here

        if raw_classes_attr_value is None:
            classes = [] # If attribute is missing, it's an empty list of classes
        elif isinstance(raw_classes_attr_value, str):
            # If it's a single string (e.g., class="myclass"), wrap it in a list
            classes = [raw_classes_attr_value]
        elif isinstance(raw_classes_attr_value, list):
            # If it's already a list (the common case), ensure all elements are strings.
            # Filter out any potential None values within the list, though unlikely for 'class'.
            classes = [str(c) for c in raw_classes_attr_value if c is not None]
        else:
            # Fallback for any unexpected type (shouldn't happen with standard HTML), default to empty list.
            # You might want to log a warning here in a real application.
            classes = []
        # --- END OF ROBUST FIX FOR CLASSES TYPE ---

        # --- Existing (and now correct) fix for ID type ---
        element_id_raw = element.get('id')
        element_id: Optional[str] = None
        if isinstance(element_id_raw, list): # Handles malformed HTML like id="['foo']"
            element_id = str(element_id_raw[0]) if element_id_raw else None
        elif element_id_raw is not None:
            element_id = str(element_id_raw)
        # --- End ID type fix ---

        text_content = ""
        if element.string:
            text_content = element.string.strip()
        elif element.get_text():
            text_content = element.get_text(strip=True)[:200]

        attributes = {k: v for k, v in element.attrs.items()
                    if k not in ['class', 'id']}

        # Ensure generate_xpath and classify_element are imported from helpers
        from ..utils.helpers import generate_xpath, classify_element
        xpath = generate_xpath(element)

        # Now, 'classes' is definitively List[str], satisfying Pylance and the classify_element signature
        element_type = classify_element(tag, classes, attributes)

        return ElementInfo(
            tag=tag,
            classes=classes, # Pass the now correctly typed 'classes'
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

    def generate_signature(self,
                           element_info: ElementInfo,
                           include_parent: bool = True,
                           depth: Optional[int] = None) -> ElementSignature: # <--- CORRECTED: depth is Optional[int]
        """Generate a hashable signature for element grouping using helper."""
        # Ensure generate_element_signature is imported from helpers
        from ..utils.helpers import generate_element_signature
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
            # Use setdefault to add a new list if the signature isn't already a key
            self._element_signatures.setdefault(signature, []).append(element)

    def get_document_stats(self) -> Dict[str, Any]:
        """Get basic statistics about the document"""
        if not self._analyzed:
            self.extract_all_elements()

        tag_counts = Counter(el.tag for el in self.elements)
        type_counts = Counter(el.element_type.value for el in self.elements)

        total_depth = sum(el.depth for el in self.elements)
        avg_depth = total_depth / len(self.elements) if self.elements else 0

        return {
            'total_elements': len(self.elements),
            'unique_tags': len(set(el.tag for el in self.elements)),
            'max_depth': max((el.depth for el in self.elements), default=0),
            'avg_depth': avg_depth,
            'elements_with_classes': sum(1 for el in self.elements if el.classes),
            'elements_with_ids': sum(1 for el in self.elements if el.id),
            'elements_with_text': sum(1 for el in self.elements if el.text),
            'most_common_tags': dict(tag_counts.most_common(10)),
            'element_types': dict(type_counts),
        }

    def detect_patterns(self,
                        min_threshold: int = 2,
                        similarity_threshold: float = 1.0,
                        pattern_signature_config: Optional[Dict[str, Any]] = None # <--- Corrected param here
                       ) -> Dict[ElementSignature, PatternInfo]:
        """
        Detects repeating HTML patterns in the document based on element signatures.
        """
        self.extract_all_elements() # Ensure elements are extracted first

        if similarity_threshold < 1.0:
            print("Warning: Fuzzy matching (similarity_threshold < 1.0) is not yet implemented. Using exact matching.")

        all_elements = self.elements

        signature_groups: Dict[ElementSignature, List[ElementInfo]] = defaultdict(list)
        for element_info in all_elements:
            # Dynamically determine signature generation parameters from config
            _include_parent = True
            _depth_for_signature = None # Default to None to use ElementInfo's depth

            if pattern_signature_config:
                _include_parent = pattern_signature_config.get('include_parent', True)
                _depth_for_signature = pattern_signature_config.get('depth', None)

            signature = self.generate_signature(
                element_info,
                include_parent=_include_parent,
                depth=_depth_for_signature # Pass 'depth' here
            )
            signature_groups[signature].append(element_info)

        detected_patterns: Dict[ElementSignature, PatternInfo] = {}
        for signature, elements_list in signature_groups.items():
            if len(elements_list) >= min_threshold:
                detected_patterns[signature] = PatternInfo(
                    signature=signature,
                    elements=elements_list,
                    count=len(elements_list),
                    confidence=1.0
                )
        return detected_patterns

    def find_potential_patterns(self, min_threshold: int = 2) -> Dict[ElementSignature, List[ElementInfo]]:
        """
        Identifies potential repeating patterns based on element signatures.
        This method now leverages detect_patterns.
        """
        # Call detect_patterns without a specific pattern_signature_config for simplicity in this method.
        # It will use the defaults from detect_patterns and generate_signature.
        patterns_info = self.detect_patterns(min_threshold=min_threshold)
        return {sig: pi.elements for sig, pi in patterns_info.items()}












# class ParsedDocument:
#     """Main document representation with analysis capabilities"""

#     def __init__(self, url: str, soup: BeautifulSoup, response_info: Dict[str, Any]):
#         self.url = url
#          html_content: str 
#         self.soup = soup
#         self.response_info = response_info
#         self.elements: List[ElementInfo] = []
#         self._element_signatures: Dict[ElementSignature, List[ElementInfo]] = {}
#         self._analyzed = False

#     def extract_all_elements(self) -> List[ElementInfo]:
#         """Extract all HTML elements with their properties and relationships"""
#         if self._analyzed:
#             print("DEBUG: extract_all_elements - Already analyzed, returning cached elements.")
#             return self.elements

#         self.elements = []
#         print("DEBUG: extract_all_elements - Starting new extraction.")

#         # This is the loop where the crucial change was made. Let's trace it.
#         for i, child_element in enumerate(self.soup.children):
#             print(f"DEBUG:   Child {i}: Type={type(child_element)}, Name={getattr(child_element, 'name', 'N/A')}, IsTag={isinstance(child_element, Tag)}")
#             if isinstance(child_element, Tag):
#                 print(f"DEBUG:     Calling _extract_recursive for {child_element.name} (depth=0).")
#                 self._extract_recursive(child_element, depth=0, parent_sig="")
#             else:
#                 print(f"DEBUG:     Skipping non-Tag child (e.g., NavigableString whitespace).")

#         self._analyzed = True
#         print(f"DEBUG: extract_all_elements - Finished. Total elements extracted: {len(self.elements)}")
#         return self.elements
    
#     # def extract_all_elements(self) -> List[ElementInfo]:
#     #     """Extract all HTML elements with their properties and relationships"""
#     #     if self._analyzed:
#     #         return self.elements

#     #     self.elements = []
#     #     self._extract_recursive(self.soup, depth=0, parent_sig="")
#     #     self._analyzed = True
#     #     return self.elements

#     def _extract_recursive(self, element, depth: int = 0, parent_sig: str = ""):
#         """Recursively extract elements and build the element tree"""
#         if not isinstance(element, Tag):
#             return

#         # Create ElementInfo for current element
#         element_info = self._create_element_info(element, depth, parent_sig)
#         self.elements.append(element_info)

#         # Get signature for this element to pass to children
#         current_sig = self._generate_signature_string(element_info)

#         # Process children
#         children = [child for child in element.children if isinstance(child, Tag)]
#         element_info.children_count = len(children)

#         for child in children:
#             self._extract_recursive(child, depth + 1, current_sig)

#     def _create_element_info(self, element: Tag, depth: int, parent_sig: str) -> ElementInfo:
#         """Create ElementInfo object from BeautifulSoup Tag"""
#         tag = element.name.lower()
#         classes = element.get('class', [])
#         element_id = element.get('id')

#         text_content = ""
#         if element.string:
#             text_content = element.string.strip()
#         elif element.get_text():
#             text_content = element.get_text(strip=True)[:200]

#         attributes = {k: v for k, v in element.attrs.items()
#                      if k not in ['class', 'id']}

#         xpath = generate_xpath(element)
#         element_type = classify_element(tag, classes, attributes)
#         # --- DEBUG PRINT ---
#         print(f"DEBUG: _create_element_info - Tag: {tag}, Classes: {classes}, ID: {element_id}")
#         # --- END DEBUG PRINT ---

#         return ElementInfo(
#             tag=tag,
#             classes=classes,
#             id=element_id,
#             text=text_content,
#             attributes=attributes,
#             parent_signature=parent_sig,
#             depth=depth,
#             xpath=xpath,
#             element_type=element_type
#         )

#     def _generate_signature_string(self, element_info: ElementInfo) -> str:
#         """Generate a string representation of element signature for parent_signature field"""
#         classes_str = ",".join(sorted(element_info.classes))
#         return f"{element_info.tag}:{classes_str}:{element_info.id or 'no-id'}"

#     def generate_signature(self, element_info: ElementInfo,
#                           include_parent: bool = True, depth: int = 2) -> ElementSignature:
#         """Generate a hashable signature for element grouping using helper."""
#         return generate_element_signature(element_info, include_parent, depth)


#     def get_elements_by_signature(self, signature: ElementSignature) -> List[ElementInfo]:
#         """Get all elements matching a specific signature"""
#         if not self._element_signatures:
#             self._build_signature_index()

#         return self._element_signatures.get(signature, [])

#     def _build_signature_index(self):
#         """Build index of elements by signature for fast lookup"""
#         self._element_signatures.clear()

#         for element in self.elements:
#             signature = self.generate_signature(element)
#             if signature not in self._element_signatures:
#                 self._element_signatures[signature] = []
#             self._element_signatures[signature].append(element)

#     def get_document_stats(self) -> Dict[str, Any]:
#         """Get basic statistics about the document"""
#         if not self._analyzed:
#             self.extract_all_elements()

#         tag_counts = Counter(el.tag for el in self.elements)
#         type_counts = Counter(el.element_type.value for el in self.elements)

#         # Calculate average depth
#         total_depth = sum(el.depth for el in self.elements)
#         avg_depth = total_depth / len(self.elements) if self.elements else 0

#         # Return the complete dictionary with all expected keys
#         return {
#             'total_elements': len(self.elements),
#             'unique_tags': len(set(el.tag for el in self.elements)),
#             'max_depth': max((el.depth for el in self.elements), default=0),
#             'avg_depth': avg_depth, # <--- ADD THIS LINE
#             'elements_with_classes': sum(1 for el in self.elements if el.classes),
#             'elements_with_ids': sum(1 for el in self.elements if el.id),
#             'elements_with_text': sum(1 for el in self.elements if el.text),
#             'most_common_tags': dict(tag_counts.most_common(10)), # <--- ADD THIS LINE
#             'element_types': dict(type_counts), # <--- ADD THIS LINE
#             # 'tag_distribution' was in your original snippet, but 'most_common_tags' is more specific for a dict.
#             # I'd recommend using 'most_common_tags' as implemented here.
#             # If you want both, just keep 'tag_distribution' too and fill it.
#         }
        
        
#     def detect_patterns(self, min_threshold: int = 2, similarity_threshold: float = 1.0, pattern_signature_config: Optional[Dict[str, Any]] = None) -> Dict[ElementSignature, PatternInfo]:
#         """
#         Detects repeating HTML patterns in the document based on element signatures.

#         Args:
#             min_threshold (int): Minimum number of occurrences for a pattern to be considered.
#             similarity_threshold (float): (Optional, for future) A float from 0.0 to 1.0
#                                          indicating how similar signatures must be to be grouped.
#                                          1.0 for exact match, less for fuzzy matching (not implemented yet).

#         Returns:
#             Dict[ElementSignature, PatternInfo]: A dictionary where keys are the signatures
#                                                  and values are PatternInfo objects containing
#                                                  details about the pattern and its matching elements.
#         """
#          # --- ADD THIS CRUCIAL LINE ---
#         self.extract_all_elements()
#         # --- END ADDITION ---

        
#         if similarity_threshold < 1.0:
#             # This is a placeholder for future fuzzy matching.
#             # For now, we only support exact matches (similarity_threshold=1.0)
#             print("Warning: Fuzzy matching (similarity_threshold < 1.0) is not yet implemented. Using exact matching.")

#         # Ensure elements are extracted if not already
#         all_elements = self.elements # This will call extract_all_elements if _elements is None

#         # Group elements by their exact signature
#         signature_groups: Dict[ElementSignature, List[ElementInfo]] = defaultdict(list)
#         for element_info in all_elements:
#             signature = self.generate_signature(element_info)
#             signature_groups[signature].append(element_info)

#         # Filter groups based on min_threshold and create PatternInfo objects
#         detected_patterns: Dict[ElementSignature, PatternInfo] = {}
#         for signature, elements_list in signature_groups.items():
#             if len(elements_list) >= min_threshold:
#                 # For now, confidence is 1.0 for exact matches. Fuzzy matching is future.
#                 detected_patterns[signature] = PatternInfo(
#                     signature=signature,
#                     elements=elements_list,
#                     # count is automatically set in PatternInfo.__post_init__
#                     # confidence is automatically set in PatternInfo.__post_init__
#                 )
#         return detected_patterns

    
    
#     # The existing find_potential_patterns should ideally just call detect_patterns
#     # Make sure your existing find_potential_patterns uses detect_patterns
#     def find_potential_patterns(self, min_threshold: int = 2) -> Dict[ElementSignature, List[ElementInfo]]:
#         """
#         Identifies potential repeating patterns based on element signatures.
#         (This method might be refactored to return PatternInfo in the future).
#         """
#         # For now, let's keep it simple and just return the list of elements directly from detect_patterns
#         # and not the full PatternInfo object as the demo expects a List[ElementInfo]
#         # This will be refined as we use PatternInfo more.
#         patterns_info = self.detect_patterns(min_threshold=min_threshold)
#         return {sig: pi.elements for sig, pi in patterns_info.items()}
    
    
    # def find_potential_patterns(self, min_threshold: int = 2) -> Dict[ElementSignature, List[ElementInfo]]:
    #     """
    #     Find elements that appear multiple times (a preview for Sprint 2 functionality).
    #     Groups elements by their ElementSignature and returns groups meeting a min_threshold.
    #     """
    #     if not self._element_signatures:
    #         self._build_signature_index()

    #     patterns = {}
    #     for signature, elements in self._element_signatures.items():
    #         if len(elements) >= min_threshold:
    #             patterns[signature] = elements

    #     return patterns