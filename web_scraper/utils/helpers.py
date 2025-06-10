import hashlib
from typing import List, Dict, Any
from bs4 import Tag

from ..core.models import ElementInfo, ElementType, ElementSignature


def generate_xpath(element: Tag) -> str:
    """Generate a simplified XPath for the element"""
    path_parts = []
    current = element

    while current and current.name:
        tag = current.name
        # Add position if there are siblings with same tag
        siblings = [s for s in current.parent.children
                   if isinstance(s, Tag) and s.name == tag] if current.parent else [current]

        if len(siblings) > 1:
            position = siblings.index(current) + 1
            path_parts.append(f"{tag}[{position}]")
        else:
            path_parts.append(tag)

        current = current.parent

    return "/" + "/".join(reversed(path_parts))


def classify_element(tag: str, classes: List[str], attributes: Dict[str, str]) -> ElementType:
    """Classify element type based on tag and attributes"""
    # Navigation elements
    if tag in ['nav', 'menu'] or any('nav' in cls.lower() for cls in classes):
        return ElementType.NAVIGATION

    # Interactive elements
    if tag in ['button', 'input', 'select', 'textarea', 'a', 'form']:
        return ElementType.INTERACTIVE

    # Metadata elements
    if tag in ['meta', 'link', 'script', 'style', 'title', 'head']:
        return ElementType.METADATA

    # Structural elements
    if tag in ['header', 'footer', 'aside', 'section', 'article', 'main']:
        return ElementType.STRUCTURAL

    return ElementType.CONTENT


def generate_element_signature(element_info: ElementInfo,
                              include_parent: bool = True, depth: int = 2) -> ElementSignature:
    """Generate a hashable signature for element grouping"""
    # Create hash of classes
    classes_sorted = sorted(element_info.classes)
    classes_hash = hashlib.md5(",".join(classes_sorted).encode()).hexdigest()[:8]

    # Parent context (simplified)
    parent_context = ""
    if include_parent and element_info.parent_signature:
        parent_parts = element_info.parent_signature.split(":")
        if len(parent_parts) >= 2:
            parent_context = f"{parent_parts[0]}:{parent_parts[1][:10]}"

    # Depth range for grouping similar depth elements
    depth_range = f"{max(0, element_info.depth-1)}-{element_info.depth+1}"

    return ElementSignature(
        tag=element_info.tag,
        classes_hash=classes_hash,
        id_present=element_info.id is not None,
        parent_context=parent_context,
        depth_range=depth_range
    )
    
def generate_signature_string(element_info: ElementInfo) -> str:
    """
    Generates a simplified, human-readable string representation of an element's signature.
    Useful for quick debugging or logging, but not for hashing/grouping.
    """
    tag = element_info.tag
    classes_str = ",".join(sorted(element_info.classes)) if element_info.classes else "no-classes"
    id_str = element_info.id if element_info.id else "no-id"
    return f"{tag}:{classes_str}:{id_str}"
