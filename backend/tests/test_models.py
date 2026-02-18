"""
Unit tests for data models.

Tests data model instantiation, field access, and type validation.
"""

import pytest
from PIL import Image
from app.models import (
    PageImage,
    WordBox,
    OCRResult,
    StructureElement,
    DocumentStructure
)


class TestPageImage:
    """Tests for PageImage data model."""
    
    def test_page_image_creation(self):
        """Test creating a PageImage instance with all fields."""
        img = Image.new('RGB', (100, 100))
        page = PageImage(
            page_number=1,
            image=img,
            width=100,
            height=100,
            dpi=300
        )
        
        assert page.page_number == 1
        assert page.image == img
        assert page.width == 100
        assert page.height == 100
        assert page.dpi == 300
    
    def test_page_image_field_access(self):
        """Test accessing individual fields of PageImage."""
        img = Image.new('RGB', (200, 300))
        page = PageImage(
            page_number=5,
            image=img,
            width=200,
            height=300,
            dpi=600
        )
        
        assert page.page_number == 5
        assert page.width == 200
        assert page.height == 300
        assert page.dpi == 600


class TestWordBox:
    """Tests for WordBox data model."""
    
    def test_word_box_creation(self):
        """Test creating a WordBox instance with all fields."""
        word = WordBox(
            text="Hello",
            x=10,
            y=20,
            width=50,
            height=15,
            confidence=0.95
        )
        
        assert word.text == "Hello"
        assert word.x == 10
        assert word.y == 20
        assert word.width == 50
        assert word.height == 15
        assert word.confidence == 0.95
    
    def test_word_box_with_special_characters(self):
        """Test WordBox with special characters and punctuation."""
        word = WordBox(
            text="Hello, World!",
            x=0,
            y=0,
            width=100,
            height=20,
            confidence=0.88
        )
        
        assert word.text == "Hello, World!"
        assert word.confidence == 0.88


class TestOCRResult:
    """Tests for OCRResult data model."""
    
    def test_ocr_result_creation(self):
        """Test creating an OCRResult with words."""
        words = [
            WordBox("Hello", 10, 20, 50, 15, 0.95),
            WordBox("World", 65, 20, 50, 15, 0.92)
        ]
        
        result = OCRResult(
            text="Hello World",
            words=words,
            confidence=0.935
        )
        
        assert result.text == "Hello World"
        assert len(result.words) == 2
        assert result.words[0].text == "Hello"
        assert result.words[1].text == "World"
        assert result.confidence == 0.935
    
    def test_ocr_result_empty_words(self):
        """Test OCRResult with no words (blank page)."""
        result = OCRResult(
            text="",
            words=[],
            confidence=0.0
        )
        
        assert result.text == ""
        assert len(result.words) == 0
        assert result.confidence == 0.0


class TestStructureElement:
    """Tests for StructureElement data model."""
    
    def test_paragraph_element(self):
        """Test creating a paragraph structure element."""
        element = StructureElement(
            type="paragraph",
            content="This is a paragraph.",
            style={"alignment": "left"}
        )
        
        assert element.type == "paragraph"
        assert element.content == "This is a paragraph."
        assert element.level == 0
        assert element.style == {"alignment": "left"}
    
    def test_heading_element(self):
        """Test creating a heading structure element with level."""
        element = StructureElement(
            type="heading",
            content="Chapter 1",
            level=1,
            style={"bold": True}
        )
        
        assert element.type == "heading"
        assert element.content == "Chapter 1"
        assert element.level == 1
        assert element.style == {"bold": True}
    
    def test_list_element(self):
        """Test creating a list structure element."""
        element = StructureElement(
            type="list",
            content="• Item 1\n• Item 2",
            style={"list_type": "bullet"}
        )
        
        assert element.type == "list"
        assert element.content == "• Item 1\n• Item 2"
        assert element.style == {"list_type": "bullet"}
    
    def test_table_element(self):
        """Test creating a table structure element."""
        element = StructureElement(
            type="table",
            content="Row1Col1|Row1Col2\nRow2Col1|Row2Col2",
            style={"rows": 2, "cols": 2}
        )
        
        assert element.type == "table"
        assert element.content == "Row1Col1|Row1Col2\nRow2Col1|Row2Col2"
        assert element.style == {"rows": 2, "cols": 2}
    
    def test_default_style(self):
        """Test that style defaults to empty dict."""
        element = StructureElement(
            type="paragraph",
            content="Test"
        )
        
        assert element.style == {}


class TestDocumentStructure:
    """Tests for DocumentStructure data model."""
    
    def test_document_structure_creation(self):
        """Test creating a DocumentStructure with multiple elements."""
        elements = [
            StructureElement(type="heading", content="Title", level=1),
            StructureElement(type="paragraph", content="First paragraph."),
            StructureElement(type="paragraph", content="Second paragraph.")
        ]
        
        doc = DocumentStructure(elements=elements)
        
        assert len(doc.elements) == 3
        assert doc.elements[0].type == "heading"
        assert doc.elements[1].type == "paragraph"
        assert doc.elements[2].type == "paragraph"
    
    def test_document_structure_empty(self):
        """Test creating an empty DocumentStructure."""
        doc = DocumentStructure(elements=[])
        
        assert len(doc.elements) == 0
    
    def test_document_structure_mixed_elements(self):
        """Test DocumentStructure with various element types."""
        elements = [
            StructureElement(type="heading", content="Introduction", level=1),
            StructureElement(type="paragraph", content="Some text."),
            StructureElement(type="list", content="• Point 1\n• Point 2"),
            StructureElement(type="table", content="Data")
        ]
        
        doc = DocumentStructure(elements=elements)
        
        assert len(doc.elements) == 4
        assert doc.elements[0].type == "heading"
        assert doc.elements[1].type == "paragraph"
        assert doc.elements[2].type == "list"
        assert doc.elements[3].type == "table"
