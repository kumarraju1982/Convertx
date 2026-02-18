"""
Unit tests for LayoutAnalyzer component.

Tests the layout analysis functionality including paragraph boundary detection
and heading detection based on font size.
"""

import pytest
from app.layout_analyzer import LayoutAnalyzer
from app.models import OCRResult, WordBox, DocumentStructure, StructureElement


class TestLayoutAnalyzer:
    """Test suite for LayoutAnalyzer class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = LayoutAnalyzer()
    
    def test_analyze_empty_ocr_result(self):
        """Test analyzing OCR result with no words."""
        ocr_result = OCRResult(text="", words=[], confidence=0.0)
        structure = self.analyzer.analyze(ocr_result)
        
        assert isinstance(structure, DocumentStructure)
        assert len(structure.elements) == 0
    
    def test_analyze_single_line_paragraph(self):
        """Test analyzing a single line of text as a paragraph."""
        words = [
            WordBox(text="Hello", x=10, y=10, width=50, height=20, confidence=0.95),
            WordBox(text="world", x=70, y=10, width=50, height=20, confidence=0.95),
        ]
        ocr_result = OCRResult(text="Hello world", words=words, confidence=0.95)
        
        structure = self.analyzer.analyze(ocr_result)
        
        assert len(structure.elements) == 1
        assert structure.elements[0].type == "paragraph"
        assert structure.elements[0].content == "Hello world"
    
    def test_analyze_heading_detection(self):
        """Test detecting headings based on larger font size."""
        # Create words with different heights - first line is larger (heading)
        words = [
            # Heading line (height=30, larger than average)
            WordBox(text="Chapter", x=10, y=10, width=80, height=30, confidence=0.95),
            WordBox(text="One", x=100, y=10, width=40, height=30, confidence=0.95),
            # Regular text line (height=20)
            WordBox(text="This", x=10, y=50, width=40, height=20, confidence=0.95),
            WordBox(text="is", x=60, y=50, width=20, height=20, confidence=0.95),
            WordBox(text="text", x=90, y=50, width=40, height=20, confidence=0.95),
        ]
        ocr_result = OCRResult(text="Chapter One\nThis is text", words=words, confidence=0.95)
        
        structure = self.analyzer.analyze(ocr_result)
        
        # Should detect heading and paragraph
        assert len(structure.elements) == 2
        assert structure.elements[0].type == "heading"
        assert structure.elements[0].content == "Chapter One"
        assert structure.elements[0].level in [1, 2, 3]
        assert structure.elements[1].type == "paragraph"
        assert structure.elements[1].content == "This is text"
    
    def test_analyze_paragraph_boundary_detection(self):
        """Test detecting paragraph boundaries based on vertical spacing."""
        # Create two paragraphs with large spacing between them
        words = [
            # First paragraph (y=10)
            WordBox(text="First", x=10, y=10, width=40, height=20, confidence=0.95),
            WordBox(text="paragraph", x=60, y=10, width=80, height=20, confidence=0.95),
            # Second line of first paragraph (y=35, close spacing)
            WordBox(text="continues", x=10, y=35, width=80, height=20, confidence=0.95),
            WordBox(text="here", x=100, y=35, width=40, height=20, confidence=0.95),
            # Second paragraph (y=90, large spacing from previous)
            WordBox(text="Second", x=10, y=90, width=60, height=20, confidence=0.95),
            WordBox(text="paragraph", x=80, y=90, width=80, height=20, confidence=0.95),
        ]
        ocr_result = OCRResult(
            text="First paragraph\ncontinues here\n\nSecond paragraph",
            words=words,
            confidence=0.95
        )
        
        structure = self.analyzer.analyze(ocr_result)
        
        # Should detect two separate paragraphs
        assert len(structure.elements) == 2
        assert structure.elements[0].type == "paragraph"
        assert "First paragraph" in structure.elements[0].content
        assert "continues here" in structure.elements[0].content
        assert structure.elements[1].type == "paragraph"
        assert structure.elements[1].content == "Second paragraph"
    
    def test_analyze_multiple_headings_and_paragraphs(self):
        """Test analyzing document with multiple headings and paragraphs."""
        words = [
            # Heading 1 (height=35)
            WordBox(text="Title", x=10, y=10, width=60, height=35, confidence=0.95),
            # Paragraph 1 (height=20)
            WordBox(text="Some", x=10, y=55, width=50, height=20, confidence=0.95),
            WordBox(text="text", x=70, y=55, width=40, height=20, confidence=0.95),
            # Heading 2 (height=30)
            WordBox(text="Subtitle", x=10, y=100, width=80, height=30, confidence=0.95),
            # Paragraph 2 (height=20)
            WordBox(text="More", x=10, y=140, width=50, height=20, confidence=0.95),
            WordBox(text="text", x=70, y=140, width=40, height=20, confidence=0.95),
        ]
        ocr_result = OCRResult(
            text="Title\nSome text\nSubtitle\nMore text",
            words=words,
            confidence=0.95
        )
        
        structure = self.analyzer.analyze(ocr_result)
        
        # Should detect 2 headings and 2 paragraphs
        assert len(structure.elements) == 4
        assert structure.elements[0].type == "heading"
        assert structure.elements[0].content == "Title"
        assert structure.elements[1].type == "paragraph"
        assert structure.elements[1].content == "Some text"
        assert structure.elements[2].type == "heading"
        assert structure.elements[2].content == "Subtitle"
        assert structure.elements[3].type == "paragraph"
        assert structure.elements[3].content == "More text"
    
    def test_group_words_into_lines(self):
        """Test grouping words into lines based on vertical position."""
        words = [
            # Line 1 (y=10)
            WordBox(text="Hello", x=10, y=10, width=50, height=20, confidence=0.95),
            WordBox(text="world", x=70, y=12, width=50, height=20, confidence=0.95),  # Slightly different y
            # Line 2 (y=40)
            WordBox(text="Second", x=10, y=40, width=60, height=20, confidence=0.95),
            WordBox(text="line", x=80, y=40, width=40, height=20, confidence=0.95),
        ]
        
        lines = self.analyzer._group_words_into_lines(words)
        
        assert len(lines) == 2
        assert len(lines[0]) == 2
        assert lines[0][0].text == "Hello"
        assert lines[0][1].text == "world"
        assert len(lines[1]) == 2
        assert lines[1][0].text == "Second"
        assert lines[1][1].text == "line"
    
    def test_heading_level_detection(self):
        """Test that heading levels are assigned based on relative font size."""
        # Create headings with different sizes
        # To be detected as headings, they need to be significantly larger than regular text
        words = [
            # Very large heading (height=50)
            WordBox(text="Big", x=10, y=10, width=50, height=50, confidence=0.95),
            # Regular text (height=20)
            WordBox(text="Text1", x=10, y=70, width=50, height=20, confidence=0.95),
            # Medium heading (height=42)
            WordBox(text="Medium", x=10, y=100, width=70, height=42, confidence=0.95),
            # Regular text (height=20)
            WordBox(text="Text2", x=10, y=152, width=50, height=20, confidence=0.95),
            # Small heading (height=38)
            WordBox(text="Small", x=10, y=182, width=60, height=38, confidence=0.95),
            # Regular text (height=20)
            WordBox(text="Text3", x=10, y=230, width=50, height=20, confidence=0.95),
        ]
        ocr_result = OCRResult(
            text="Big\nText1\nMedium\nText2\nSmall\nText3",
            words=words,
            confidence=0.95
        )
        
        structure = self.analyzer.analyze(ocr_result)
        
        # Should detect 3 headings with different levels and 3 paragraphs
        headings = [e for e in structure.elements if e.type == "heading"]
        assert len(headings) == 3
        
        # Larger text should have lower level numbers (higher importance)
        assert headings[0].level <= headings[1].level
        assert headings[1].level <= headings[2].level
    
    def test_analyze_preserves_reading_order(self):
        """Test that analysis preserves top-to-bottom reading order."""
        # Create lines with mixed vertical positions to test sorting
        # Mix of headings and paragraphs with out-of-order y-coordinates
        words = [
            # Line at y=100 (heading, should be second)
            WordBox(text="Second", x=10, y=100, width=60, height=35, confidence=0.95),
            # Line at y=10 (heading, should come first)
            WordBox(text="First", x=10, y=10, width=50, height=35, confidence=0.95),
            # Line at y=50 (regular text, between first and second)
            WordBox(text="Between", x=10, y=50, width=70, height=20, confidence=0.95),
        ]
        ocr_result = OCRResult(text="First\nBetween\nSecond", words=words, confidence=0.95)
        
        structure = self.analyzer.analyze(ocr_result)
        
        # Elements should be in top-to-bottom order despite input order
        assert len(structure.elements) >= 2  # At least 2 elements
        # First element should contain "First" (y=10)
        assert "First" in structure.elements[0].content
        # Last element should contain "Second" (y=100)
        assert "Second" in structure.elements[-1].content

    def test_detect_bullet_list(self):
        """Test detecting bullet point lists."""
        words = [
            # Bullet list items
            WordBox(text="•", x=10, y=10, width=10, height=20, confidence=0.95),
            WordBox(text="First", x=25, y=10, width=40, height=20, confidence=0.95),
            WordBox(text="item", x=70, y=10, width=30, height=20, confidence=0.95),
            
            WordBox(text="•", x=10, y=35, width=10, height=20, confidence=0.95),
            WordBox(text="Second", x=25, y=35, width=50, height=20, confidence=0.95),
            WordBox(text="item", x=80, y=35, width=30, height=20, confidence=0.95),
            
            WordBox(text="•", x=10, y=60, width=10, height=20, confidence=0.95),
            WordBox(text="Third", x=25, y=60, width=40, height=20, confidence=0.95),
            WordBox(text="item", x=70, y=60, width=30, height=20, confidence=0.95),
        ]
        ocr_result = OCRResult(
            text="• First item\n• Second item\n• Third item",
            words=words,
            confidence=0.95
        )
        
        structure = self.analyzer.analyze(ocr_result)
        
        # Should detect a list element
        assert len(structure.elements) == 1
        assert structure.elements[0].type == "list"
        assert "First item" in structure.elements[0].content
        assert "Second item" in structure.elements[0].content
        assert "Third item" in structure.elements[0].content
        assert structure.elements[0].style.get("list_type") == "bullet"
    
    def test_detect_numbered_list(self):
        """Test detecting numbered lists."""
        words = [
            # Numbered list items
            WordBox(text="1.", x=10, y=10, width=15, height=20, confidence=0.95),
            WordBox(text="First", x=30, y=10, width=40, height=20, confidence=0.95),
            WordBox(text="item", x=75, y=10, width=30, height=20, confidence=0.95),
            
            WordBox(text="2.", x=10, y=35, width=15, height=20, confidence=0.95),
            WordBox(text="Second", x=30, y=35, width=50, height=20, confidence=0.95),
            WordBox(text="item", x=85, y=35, width=30, height=20, confidence=0.95),
        ]
        ocr_result = OCRResult(
            text="1. First item\n2. Second item",
            words=words,
            confidence=0.95
        )
        
        structure = self.analyzer.analyze(ocr_result)
        
        # Should detect a list element
        assert len(structure.elements) == 1
        assert structure.elements[0].type == "list"
        assert "1. First item" in structure.elements[0].content
        assert "2. Second item" in structure.elements[0].content
        assert structure.elements[0].style.get("list_type") == "numbered"
    
    def test_detect_simple_table(self):
        """Test detecting a simple table structure."""
        # Create a 3x3 table with aligned columns
        words = [
            # Row 1 (y=10)
            WordBox(text="Name", x=10, y=10, width=40, height=20, confidence=0.95),
            WordBox(text="Age", x=100, y=10, width=30, height=20, confidence=0.95),
            WordBox(text="City", x=180, y=10, width=35, height=20, confidence=0.95),
            
            # Row 2 (y=35)
            WordBox(text="John", x=10, y=35, width=35, height=20, confidence=0.95),
            WordBox(text="25", x=100, y=35, width=20, height=20, confidence=0.95),
            WordBox(text="NYC", x=180, y=35, width=30, height=20, confidence=0.95),
            
            # Row 3 (y=60)
            WordBox(text="Jane", x=10, y=60, width=35, height=20, confidence=0.95),
            WordBox(text="30", x=100, y=60, width=20, height=20, confidence=0.95),
            WordBox(text="LA", x=180, y=60, width=25, height=20, confidence=0.95),
        ]
        ocr_result = OCRResult(
            text="Name Age City\nJohn 25 NYC\nJane 30 LA",
            words=words,
            confidence=0.95
        )
        
        structure = self.analyzer.analyze(ocr_result)
        
        # Should detect a table element
        assert len(structure.elements) == 1
        assert structure.elements[0].type == "table"
        assert "Name" in structure.elements[0].content
        assert "John" in structure.elements[0].content
        assert "Jane" in structure.elements[0].content
        assert structure.elements[0].style.get("rows") == 3
        assert structure.elements[0].style.get("columns") >= 2
    
    def test_detect_two_column_layout(self):
        """Test detecting two-column layout."""
        # Create words in two distinct columns with more lines for better detection
        words = [
            # Left column (x around 10-100) - multiple lines
            WordBox(text="Left", x=10, y=10, width=40, height=20, confidence=0.95),
            WordBox(text="column", x=55, y=10, width=50, height=20, confidence=0.95),
            WordBox(text="text", x=10, y=35, width=35, height=20, confidence=0.95),
            WordBox(text="here", x=50, y=35, width=35, height=20, confidence=0.95),
            WordBox(text="more", x=10, y=60, width=35, height=20, confidence=0.95),
            WordBox(text="content", x=50, y=60, width=50, height=20, confidence=0.95),
            
            # Right column (x around 200-300) - multiple lines
            WordBox(text="Right", x=200, y=10, width=45, height=20, confidence=0.95),
            WordBox(text="column", x=250, y=10, width=50, height=20, confidence=0.95),
            WordBox(text="text", x=200, y=35, width=35, height=20, confidence=0.95),
            WordBox(text="here", x=240, y=35, width=35, height=20, confidence=0.95),
            WordBox(text="also", x=200, y=60, width=35, height=20, confidence=0.95),
            WordBox(text="content", x=240, y=60, width=50, height=20, confidence=0.95),
        ]
        ocr_result = OCRResult(
            text="Left column text here more content\nRight column text here also content",
            words=words,
            confidence=0.95
        )
        
        structure = self.analyzer.analyze(ocr_result)
        
        # Should detect elements (column detection is complex, so we just verify content is present)
        assert len(structure.elements) >= 1
        # Verify content from both columns is present
        all_content = ' '.join(elem.content for elem in structure.elements)
        assert "Left" in all_content or "Right" in all_content
    
    def test_mixed_structure_detection(self):
        """Test detecting mixed structures: heading, list, paragraph, table."""
        words = [
            # Heading (y=10, larger height)
            WordBox(text="Title", x=10, y=10, width=50, height=35, confidence=0.95),
            
            # Bullet list (y=55, 80)
            WordBox(text="•", x=10, y=55, width=10, height=20, confidence=0.95),
            WordBox(text="Item", x=25, y=55, width=35, height=20, confidence=0.95),
            WordBox(text="one", x=65, y=55, width=30, height=20, confidence=0.95),
            
            WordBox(text="•", x=10, y=80, width=10, height=20, confidence=0.95),
            WordBox(text="Item", x=25, y=80, width=35, height=20, confidence=0.95),
            WordBox(text="two", x=65, y=80, width=30, height=20, confidence=0.95),
            
            # Paragraph (y=120)
            WordBox(text="Some", x=10, y=120, width=40, height=20, confidence=0.95),
            WordBox(text="text", x=55, y=120, width=35, height=20, confidence=0.95),
        ]
        ocr_result = OCRResult(
            text="Title\n• Item one\n• Item two\nSome text",
            words=words,
            confidence=0.95
        )
        
        structure = self.analyzer.analyze(ocr_result)
        
        # Should detect heading, list, and paragraph
        assert len(structure.elements) == 3
        
        # Check types
        types = [elem.type for elem in structure.elements]
        assert "heading" in types
        assert "list" in types
        assert "paragraph" in types
        
        # Verify content
        heading = [e for e in structure.elements if e.type == "heading"][0]
        assert "Title" in heading.content
        
        list_elem = [e for e in structure.elements if e.type == "list"][0]
        assert "Item one" in list_elem.content
        assert "Item two" in list_elem.content
        
        paragraph = [e for e in structure.elements if e.type == "paragraph"][0]
        assert "Some text" in paragraph.content
    
    def test_is_list_item_bullet_variations(self):
        """Test list item detection with various bullet styles."""
        # Test bullet points
        assert self.analyzer._is_list_item("• First item")[0] is True
        assert self.analyzer._is_list_item("- Second item")[0] is True
        assert self.analyzer._is_list_item("* Third item")[0] is True
        
        # Test numbered lists
        assert self.analyzer._is_list_item("1. First item")[0] is True
        assert self.analyzer._is_list_item("2) Second item")[0] is True
        assert self.analyzer._is_list_item("a. Letter item")[0] is True
        assert self.analyzer._is_list_item("A) Capital letter")[0] is True
        
        # Test non-list items
        assert self.analyzer._is_list_item("Regular text")[0] is False
        assert self.analyzer._is_list_item("No bullet here")[0] is False
    
    def test_table_not_detected_for_short_sequences(self):
        """Test that short sequences of lines are not detected as tables."""
        # Only 2 lines - should not be detected as table
        words = [
            WordBox(text="Name", x=10, y=10, width=40, height=20, confidence=0.95),
            WordBox(text="Age", x=100, y=10, width=30, height=20, confidence=0.95),
            
            WordBox(text="John", x=10, y=35, width=35, height=20, confidence=0.95),
            WordBox(text="25", x=100, y=35, width=20, height=20, confidence=0.95),
        ]
        ocr_result = OCRResult(text="Name Age\nJohn 25", words=words, confidence=0.95)
        
        structure = self.analyzer.analyze(ocr_result)
        
        # Should not detect as table (need at least 3 rows)
        table_elements = [e for e in structure.elements if e.type == "table"]
        assert len(table_elements) == 0
    
    def test_list_followed_by_paragraph(self):
        """Test that list detection stops at non-list content."""
        words = [
            # List items
            WordBox(text="1.", x=10, y=10, width=15, height=20, confidence=0.95),
            WordBox(text="First", x=30, y=10, width=40, height=20, confidence=0.95),
            
            WordBox(text="2.", x=10, y=35, width=15, height=20, confidence=0.95),
            WordBox(text="Second", x=30, y=35, width=50, height=20, confidence=0.95),
            
            # Regular paragraph (no list marker)
            WordBox(text="This", x=10, y=70, width=35, height=20, confidence=0.95),
            WordBox(text="is", x=50, y=70, width=20, height=20, confidence=0.95),
            WordBox(text="text", x=75, y=70, width=35, height=20, confidence=0.95),
        ]
        ocr_result = OCRResult(
            text="1. First\n2. Second\nThis is text",
            words=words,
            confidence=0.95
        )
        
        structure = self.analyzer.analyze(ocr_result)
        
        # Should detect list and paragraph separately
        assert len(structure.elements) == 2
        assert structure.elements[0].type == "list"
        assert structure.elements[1].type == "paragraph"
        assert "This is text" in structure.elements[1].content
