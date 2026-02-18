"""
Unit tests for DocumentParser component.

Tests PDF validation, page extraction, and error handling.
"""

import os
import tempfile
import pytest
from PIL import Image
import fitz  # PyMuPDF

from app.document_parser import DocumentParser
from app.exceptions import PDFValidationError, FileIOError


class TestDocumentParser:
    """Test suite for DocumentParser class."""
    
    @pytest.fixture
    def parser(self):
        """Create a DocumentParser instance for testing."""
        return DocumentParser(dpi=150)  # Use lower DPI for faster tests
    
    @pytest.fixture
    def sample_pdf(self):
        """Create a temporary PDF file with 2 pages for testing."""
        # Create a temporary PDF file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_path = temp_file.name
        temp_file.close()
        
        # Create a simple 2-page PDF using PyMuPDF
        doc = fitz.open()
        
        # Page 1
        page1 = doc.new_page(width=595, height=842)  # A4 size
        page1.insert_text((50, 50), "Page 1 Content", fontsize=12)
        
        # Page 2
        page2 = doc.new_page(width=595, height=842)
        page2.insert_text((50, 50), "Page 2 Content", fontsize=12)
        
        doc.save(temp_path)
        doc.close()
        
        yield temp_path
        
        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)
    
    @pytest.fixture
    def empty_pdf(self):
        """Create a temporary empty PDF file for testing."""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_path = temp_file.name
        temp_file.close()
        
        # Write minimal PDF header that PyMuPDF will recognize as empty
        # This creates a technically valid but empty PDF structure
        with open(temp_path, 'wb') as f:
            f.write(b'%PDF-1.4\n')
            f.write(b'1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n')
            f.write(b'2 0 obj\n<< /Type /Pages /Count 0 /Kids [] >>\nendobj\n')
            f.write(b'xref\n0 3\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n')
            f.write(b'trailer\n<< /Size 3 /Root 1 0 R >>\nstartxref\n110\n%%EOF\n')
        
        yield temp_path
        
        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)
    
    @pytest.fixture
    def corrupted_pdf(self):
        """Create a corrupted PDF file for testing."""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_path = temp_file.name
        
        # Write invalid PDF content
        temp_file.write(b"This is not a valid PDF file")
        temp_file.close()
        
        yield temp_path
        
        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)
    
    # Test get_page_count method
    
    def test_get_page_count_valid_pdf(self, parser, sample_pdf):
        """Test getting page count from a valid PDF."""
        count = parser.get_page_count(sample_pdf)
        assert count == 2
    
    def test_get_page_count_nonexistent_file(self, parser):
        """Test get_page_count with non-existent file."""
        with pytest.raises(FileIOError) as exc_info:
            parser.get_page_count("/nonexistent/file.pdf")
        
        assert "not found" in str(exc_info.value).lower()
        assert exc_info.value.details["path"] == "/nonexistent/file.pdf"
    
    def test_get_page_count_empty_pdf(self, parser, empty_pdf):
        """Test get_page_count with empty PDF (no pages)."""
        with pytest.raises(PDFValidationError) as exc_info:
            parser.get_page_count(empty_pdf)
        
        assert "no pages" in str(exc_info.value).lower()
    
    def test_get_page_count_corrupted_pdf(self, parser, corrupted_pdf):
        """Test get_page_count with corrupted PDF."""
        with pytest.raises(PDFValidationError) as exc_info:
            parser.get_page_count(corrupted_pdf)
        
        assert "invalid" in str(exc_info.value).lower() or "corrupted" in str(exc_info.value).lower()
    
    def test_get_page_count_directory_path(self, parser):
        """Test get_page_count with directory path instead of file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with pytest.raises(FileIOError) as exc_info:
                parser.get_page_count(temp_dir)
            
            assert "not a file" in str(exc_info.value).lower()
    
    # Test extract_pages method
    
    def test_extract_pages_valid_pdf(self, parser, sample_pdf):
        """Test extracting pages from a valid PDF."""
        pages = parser.extract_pages(sample_pdf)
        
        # Should have 2 pages
        assert len(pages) == 2
        
        # Check first page
        assert pages[0].page_number == 1
        assert isinstance(pages[0].image, Image.Image)
        assert pages[0].width > 0
        assert pages[0].height > 0
        assert pages[0].dpi == 150
        
        # Check second page
        assert pages[1].page_number == 2
        assert isinstance(pages[1].image, Image.Image)
        assert pages[1].width > 0
        assert pages[1].height > 0
        assert pages[1].dpi == 150
    
    def test_extract_pages_maintains_order(self, parser, sample_pdf):
        """Test that pages are extracted in correct order."""
        pages = parser.extract_pages(sample_pdf)
        
        # Verify page numbers are sequential
        for i, page in enumerate(pages):
            assert page.page_number == i + 1
    
    def test_extract_pages_nonexistent_file(self, parser):
        """Test extract_pages with non-existent file."""
        with pytest.raises(FileIOError) as exc_info:
            parser.extract_pages("/nonexistent/file.pdf")
        
        assert "not found" in str(exc_info.value).lower()
    
    def test_extract_pages_empty_pdf(self, parser, empty_pdf):
        """Test extract_pages with empty PDF."""
        with pytest.raises(PDFValidationError) as exc_info:
            parser.extract_pages(empty_pdf)
        
        assert "no pages" in str(exc_info.value).lower()
    
    def test_extract_pages_corrupted_pdf(self, parser, corrupted_pdf):
        """Test extract_pages with corrupted PDF."""
        with pytest.raises(PDFValidationError) as exc_info:
            parser.extract_pages(corrupted_pdf)
        
        assert "invalid" in str(exc_info.value).lower() or "corrupted" in str(exc_info.value).lower()
    
    def test_extract_pages_directory_path(self, parser):
        """Test extract_pages with directory path instead of file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with pytest.raises(FileIOError) as exc_info:
                parser.extract_pages(temp_dir)
            
            assert "not a file" in str(exc_info.value).lower()
    
    def test_extract_pages_custom_dpi(self, sample_pdf):
        """Test extracting pages with custom DPI."""
        parser_300 = DocumentParser(dpi=300)
        pages_300 = parser_300.extract_pages(sample_pdf)
        
        parser_150 = DocumentParser(dpi=150)
        pages_150 = parser_150.extract_pages(sample_pdf)
        
        # Higher DPI should produce larger images
        assert pages_300[0].width > pages_150[0].width
        assert pages_300[0].height > pages_150[0].height
        
        # DPI should be set correctly
        assert pages_300[0].dpi == 300
        assert pages_150[0].dpi == 150
    
    def test_extract_pages_image_format(self, parser, sample_pdf):
        """Test that extracted images are in correct format."""
        pages = parser.extract_pages(sample_pdf)
        
        for page in pages:
            # Image should be PIL Image
            assert isinstance(page.image, Image.Image)
            
            # Image should have RGB mode (from PPM conversion)
            assert page.image.mode == "RGB"
            
            # Image dimensions should match reported dimensions
            assert page.image.width == page.width
            assert page.image.height == page.height
