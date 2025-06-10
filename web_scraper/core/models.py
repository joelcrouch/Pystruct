from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum


class ElementType(Enum):
    """Enum for different types of HTML elements"""
    CONTENT = "content"
    NAVIGATION = "navigation"
    STRUCTURAL = "structural"
    INTERACTIVE = "interactive"
    METADATA = "metadata"


@dataclass
class ElementInfo:
    """Core data structure representing an HTML element with all its properties"""
    tag: str
    classes: List[str] = field(default_factory=list)
    id: Optional[str] = None
    text: str = ""
    attributes: Dict[str, str] = field(default_factory=dict)
    parent_signature: str = ""
    depth: int = 0
    xpath: str = ""
    element_type: ElementType = ElementType.CONTENT
    children_count: int = 0

    def __post_init__(self):
        """Clean up text content and normalize attributes"""
        self.text = ' '.join(self.text.split()) if self.text else ""
        self.classes = [cls.strip() for cls in self.classes if cls.strip()]


@dataclass
class ElementSignature:
    """Hashable signature for grouping similar elements"""
    tag: str
    classes_hash: str
    id_present: bool
    parent_context: str
    depth_range: str  # e.g., "3-5" for elements at depth 3-5

    def __hash__(self):
        return hash((self.tag, self.classes_hash, self.id_present,
                    self.parent_context, self.depth_range))

    def __eq__(self, other):
        return (isinstance(other, ElementSignature) and
                self.tag == other.tag and
                self.classes_hash == other.classes_hash and
                self.id_present == other.id_present and
                self.parent_context == other.parent_context and
                self.depth_range == other.depth_range)

# (Add PatternInfo and SearchMatch here when implementing later sprints,
# as defined in the sprint plan's Core Data Models)
# @dataclass
# class PatternInfo:
#     signature: ElementSignature
#     elements: List[ElementInfo]
#     count: int
#     confidence: float
#     field_mappings: Dict[str, str]

# @dataclass
# class SearchMatch:
#     element: ElementInfo
#     matched_text: str
#     pattern: str
#     confidence: float