"""
Data models for PDF to Word conversion pipeline.

This module defines the core data structures used throughout the conversion process,
from PDF page extraction through OCR to document structure analysis.
"""

from dataclasses import dataclass, field
from typing import List, Literal
from PIL import Image


@dataclass
class PageImage:
    """
    Represents a single page extracted from a PDF as an image.
    
    Attributes:
        page_number: The page number in the original PDF (1-indexed)
        image: PIL Image object containing the page content
        width: Image width in pixels
        height: Image height in pixels
        dpi: Resolution in dots per inch
    """
    page_number: int
    image: Image.Image
    width: int
    height: int
    dpi: int


@dataclass
class WordBox:
    """
    Represents a single word detected by OCR with its position and confidence.
    
    Attributes:
        text: The recognized text content
        x: X-coordinate of the top-left corner
        y: Y-coordinate of the top-left corner
        width: Width of the bounding box
        height: Height of the bounding box
        confidence: OCR confidence score (0.0 to 1.0)
    """
    text: str
    x: int
    y: int
    width: int
    height: int
    confidence: float


@dataclass
class OCRResult:
    """
    Contains the complete OCR output for a page image.
    
    Attributes:
        text: Full extracted text content
        words: List of individual words with position information
        confidence: Overall confidence score for the page (0.0 to 1.0)
    """
    text: str
    words: List[WordBox]
    confidence: float


@dataclass
class StructureElement:
    """
    Represents a detected document structure element (paragraph, heading, list, table).
    
    This is a discriminated union type where the 'type' field determines which
    additional fields are relevant.
    
    Attributes:
        type: The type of structure element
        content: The text content of the element
        level: Heading level (1-6), only relevant for type='heading'
        style: Additional styling information as a dictionary
    """
    type: Literal["paragraph", "heading", "list", "table"]
    content: str
    level: int = 0  # Only used for headings (1-6)
    style: dict = field(default_factory=dict)


@dataclass
class DocumentStructure:
    """
    Represents the complete analyzed structure of a document page.
    
    Attributes:
        elements: List of structure elements detected in the page
    """
    elements: List[StructureElement]
