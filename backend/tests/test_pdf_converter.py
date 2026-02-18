"""
Unit tests for PDFConverter class.

Tests the orchestration of the conversion pipeline including validation,
error handling, and multi-page processing.
"""

import pytest
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
from PIL import Image
from app.pdf_converter import PDFConverter
from app.models import PageImage, OCRResult, WordBox, DocumentStructure, StructureElement
from app.exceptions import PDFValidationError, OCRProcessingError, WordGenerationError


class TestPDFConverter:
    """Test suite for PDFConverter class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.converter = PDFConverter()
    
    def test_validate_pdf_nonexistent_file(self):
        """Test validation of non-existent PDF file."""
        result = self.converter.validate_pdf("/nonexistent/file.pdf")
        
        assert result["valid"] is False
        assert "not found" in result["error"]
        assert result["page_count"] is None
    
    @patch('app.pdf_converter.DocumentParser')
    def test_validate_pdf_empty_file(self, mock_parser_class):
        """Test validation of empty PDF file."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            # Mock parser to return 0 pages
            mock_parser = Mock()
            mock_parser.get_page_count.return_value = 0
            mock_parser_class.return_value = mock_parser
            
            # Create new converter with mocked parser
            converter = PDFConverter()
            result = converter.validate_pdf(tmp_path)
            
            assert result["valid"] is False
            assert "empty" in result["error"]
            assert result["page_count"] is None
        finally:
            os.remove(tmp_path)
    
    @patch('app.pdf_converter.DocumentParser')
    def test_validate_pdf_valid_file(self, mock_parser_class):
        """Test validation of valid PDF file."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            # Mock parser to return 3 pages
            mock_parser = Mock()
            mock_parser.get_page_count.return_value = 3
            mock_parser_class.return_value = mock_parser
            
            # Create new converter with mocked parser
            converter = PDFConverter()
            result = converter.validate_pdf(tmp_path)
            
            assert result["valid"] is True
            assert result["error"] is None
            assert result["page_count"] == 3
        finally:
            os.remove(tmp_path)
    
    @patch('app.pdf_converter.DocumentParser')
    def test_validate_pdf_corrupted_file(self, mock_parser_class):
        """Test validation of corrupted PDF file."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            # Mock parser to raise exception
            mock_parser = Mock()
            mock_parser.get_page_count.side_effect = Exception("Corrupted PDF")
            mock_parser_class.return_value = mock_parser
            
            # Create new converter with mocked parser
            converter = PDFConverter()
            result = converter.validate_pdf(tmp_path)
            
            assert result["valid"] is False
            assert "Invalid or corrupted" in result["error"]
            assert result["page_count"] is None
        finally:
            os.remove(tmp_path)
    
    def test_convert_nonexistent_file(self):
        """Test conversion of non-existent PDF file."""
        with pytest.raises(PDFValidationError) as exc_info:
            self.converter.convert("/nonexistent/file.pdf")
        
        assert "not found" in str(exc_info.value)
    
    @patch('os.path.isfile', return_value=True)
    @patch('os.access', return_value=True)
    @patch('os.path.exists', return_value=True)
    @patch('app.pdf_converter.DocumentParser')
    @patch('app.pdf_converter.OCREngine')
    @patch('app.pdf_converter.LayoutAnalyzer')
    @patch('app.pdf_converter.WordGenerator')
    def test_convert_single_page_success(
        self,
        mock_word_gen_class,
        mock_layout_class,
        mock_ocr_class,
        mock_parser_class,
        mock_exists,
        mock_access,
        mock_isfile
    ):
        """Test successful conversion of single-page PDF."""
        pdf_path = "/fake/test.pdf"
        output_path = "/fake/test.docx"
        
        # Mock parser
        mock_parser = Mock()
        mock_parser.get_page_count.return_value = 1
        mock_image = Image.new('RGB', (100, 100))
        mock_parser.extract_pages.return_value = [
            PageImage(page_number=1, image=mock_image, width=100, height=100, dpi=300)
        ]
        mock_parser_class.return_value = mock_parser
        
        # Mock OCR engine
        mock_ocr = Mock()
        mock_ocr.extract_text.return_value = OCRResult(
            text="Test content",
            words=[WordBox(text="Test", x=10, y=10, width=50, height=20, confidence=0.95)],
            confidence=0.95
        )
        mock_ocr_class.return_value = mock_ocr
        
        # Mock layout analyzer
        mock_layout = Mock()
        mock_layout.analyze.return_value = DocumentStructure(
            elements=[StructureElement(type="paragraph", content="Test content", style={})]
        )
        mock_layout_class.return_value = mock_layout
        
        # Mock word generator
        mock_word_gen = Mock()
        mock_doc = Mock()
        mock_word_gen.create_document.return_value = mock_doc
        mock_word_gen.save.return_value = True
        mock_word_gen_class.return_value = mock_word_gen
        
        # Create converter with mocked components
        converter = PDFConverter()
        result = converter.convert(pdf_path, output_path)
        
        assert result["success"] is True
        assert result["output_path"] == output_path
        assert result["pages_processed"] == 1
        assert result["pages_failed"] == []
        assert result["errors"] == []
        
        # Verify components were called
        mock_parser.extract_pages.assert_called_once_with(pdf_path)
        mock_ocr.extract_text.assert_called_once()
        mock_layout.analyze.assert_called_once()
        mock_word_gen.create_document.assert_called_once()
        mock_word_gen.save.assert_called_once()
    
    @patch('os.path.isfile', return_value=True)
    @patch('os.access', return_value=True)
    @patch('os.path.exists', return_value=True)
    @patch('app.pdf_converter.DocumentParser')
    @patch('app.pdf_converter.OCREngine')
    @patch('app.pdf_converter.LayoutAnalyzer')
    @patch('app.pdf_converter.WordGenerator')
    def test_convert_multi_page_success(
        self,
        mock_word_gen_class,
        mock_layout_class,
        mock_ocr_class,
        mock_parser_class,
        mock_exists,
        mock_access,
        mock_isfile
    ):
        """Test successful conversion of multi-page PDF."""
        pdf_path = "/fake/test.pdf"
        output_path = "/fake/test.docx"
        
        # Mock parser with 3 pages
        mock_parser = Mock()
        mock_parser.get_page_count.return_value = 3
        mock_image = Image.new('RGB', (100, 100))
        mock_parser.extract_pages.return_value = [
            PageImage(page_number=i, image=mock_image, width=100, height=100, dpi=300)
            for i in range(1, 4)
        ]
        mock_parser_class.return_value = mock_parser
        
        # Mock OCR engine
        mock_ocr = Mock()
        mock_ocr.extract_text.return_value = OCRResult(
            text="Test content",
            words=[WordBox(text="Test", x=10, y=10, width=50, height=20, confidence=0.95)],
            confidence=0.95
        )
        mock_ocr_class.return_value = mock_ocr
        
        # Mock layout analyzer
        mock_layout = Mock()
        mock_layout.analyze.return_value = DocumentStructure(
            elements=[StructureElement(type="paragraph", content="Test content", style={})]
        )
        mock_layout_class.return_value = mock_layout
        
        # Mock word generator
        mock_word_gen = Mock()
        mock_doc = Mock()
        mock_word_gen.create_document.return_value = mock_doc
        mock_word_gen.save.return_value = True
        mock_word_gen_class.return_value = mock_word_gen
        
        # Create converter with mocked components
        converter = PDFConverter()
        result = converter.convert(pdf_path, output_path)
        
        assert result["success"] is True
        assert result["pages_processed"] == 3
        assert result["pages_failed"] == []
        assert result["errors"] == []
        
        # Verify OCR was called 3 times
        assert mock_ocr.extract_text.call_count == 3
        assert mock_layout.analyze.call_count == 3
    
    @patch('os.path.isfile', return_value=True)
    @patch('os.access', return_value=True)
    @patch('os.path.exists', return_value=True)
    @patch('app.pdf_converter.DocumentParser')
    @patch('app.pdf_converter.OCREngine')
    @patch('app.pdf_converter.LayoutAnalyzer')
    @patch('app.pdf_converter.WordGenerator')
    def test_convert_with_page_failure(
        self,
        mock_word_gen_class,
        mock_layout_class,
        mock_ocr_class,
        mock_parser_class,
        mock_exists,
        mock_access,
        mock_isfile
    ):
        """Test conversion continues when some pages fail."""
        pdf_path = "/fake/test.pdf"
        output_path = "/fake/test.docx"
        
        # Mock parser with 3 pages
        mock_parser = Mock()
        mock_parser.get_page_count.return_value = 3
        mock_image = Image.new('RGB', (100, 100))
        mock_parser.extract_pages.return_value = [
            PageImage(page_number=i, image=mock_image, width=100, height=100, dpi=300)
            for i in range(1, 4)
        ]
        mock_parser_class.return_value = mock_parser
        
        # Mock OCR engine - fail on page 2
        mock_ocr = Mock()
        def ocr_side_effect(image):
            if mock_ocr.extract_text.call_count == 2:
                raise OCRProcessingError("OCR failed on page 2")
            return OCRResult(
                text="Test content",
                words=[WordBox(text="Test", x=10, y=10, width=50, height=20, confidence=0.95)],
                confidence=0.95
            )
        mock_ocr.extract_text.side_effect = ocr_side_effect
        mock_ocr_class.return_value = mock_ocr
        
        # Mock layout analyzer
        mock_layout = Mock()
        mock_layout.analyze.return_value = DocumentStructure(
            elements=[StructureElement(type="paragraph", content="Test content", style={})]
        )
        mock_layout_class.return_value = mock_layout
        
        # Mock word generator
        mock_word_gen = Mock()
        mock_doc = Mock()
        mock_word_gen.create_document.return_value = mock_doc
        mock_word_gen.save.return_value = True
        mock_word_gen_class.return_value = mock_word_gen
        
        # Create converter with mocked components
        converter = PDFConverter()
        result = converter.convert(pdf_path, output_path)
        
        assert result["success"] is True
        assert result["pages_processed"] == 2  # 2 out of 3 succeeded
        assert result["pages_failed"] == [2]
        assert len(result["errors"]) == 1
        assert "Page 2" in result["errors"][0]
        
        # Verify document was still created with all 3 structures (one empty)
        mock_word_gen.create_document.assert_called_once()
        structures = mock_word_gen.create_document.call_args[0][0]
        assert len(structures) == 3
    
    @patch('os.path.isfile', return_value=True)
    @patch('os.access', return_value=True)
    @patch('os.path.exists', return_value=True)
    @patch('app.pdf_converter.DocumentParser')
    @patch('app.pdf_converter.OCREngine')
    @patch('app.pdf_converter.LayoutAnalyzer')
    @patch('app.pdf_converter.WordGenerator')
    def test_convert_with_progress_callback(
        self,
        mock_word_gen_class,
        mock_layout_class,
        mock_ocr_class,
        mock_parser_class,
        mock_exists,
        mock_access,
        mock_isfile
    ):
        """Test that progress callback is called during conversion."""
        pdf_path = "/fake/test.pdf"
        output_path = "/fake/test.docx"
        
        # Mock parser with 2 pages
        mock_parser = Mock()
        mock_parser.get_page_count.return_value = 2
        mock_image = Image.new('RGB', (100, 100))
        mock_parser.extract_pages.return_value = [
            PageImage(page_number=i, image=mock_image, width=100, height=100, dpi=300)
            for i in range(1, 3)
        ]
        mock_parser_class.return_value = mock_parser
        
        # Mock OCR engine
        mock_ocr = Mock()
        mock_ocr.extract_text.return_value = OCRResult(
            text="Test",
            words=[],
            confidence=0.95
        )
        mock_ocr_class.return_value = mock_ocr
        
        # Mock layout analyzer
        mock_layout = Mock()
        mock_layout.analyze.return_value = DocumentStructure(elements=[])
        mock_layout_class.return_value = mock_layout
        
        # Mock word generator
        mock_word_gen = Mock()
        mock_doc = Mock()
        mock_word_gen.create_document.return_value = mock_doc
        mock_word_gen.save.return_value = True
        mock_word_gen_class.return_value = mock_word_gen
        
        # Create progress callback mock
        progress_callback = Mock()
        
        # Create converter and run conversion
        converter = PDFConverter()
        result = converter.convert(pdf_path, output_path, progress_callback=progress_callback)
        
        assert result["success"] is True
        
        # Verify progress callback was called twice (once per page)
        assert progress_callback.call_count == 2
        progress_callback.assert_any_call(1, 2)
        progress_callback.assert_any_call(2, 2)
    
    @patch('os.path.isfile', return_value=True)
    @patch('os.access', return_value=True)
    @patch('os.path.exists', return_value=True)
    @patch('app.pdf_converter.DocumentParser')
    @patch('app.pdf_converter.OCREngine')
    @patch('app.pdf_converter.LayoutAnalyzer')
    @patch('app.pdf_converter.WordGenerator')
    def test_convert_default_output_path(
        self,
        mock_word_gen_class,
        mock_layout_class,
        mock_ocr_class,
        mock_parser_class,
        mock_exists,
        mock_access,
        mock_isfile
    ):
        """Test that default output path is generated correctly."""
        pdf_path = "/fake/test.pdf"
        expected_output = "/fake/test.docx"
        
        # Mock all components
        mock_parser = Mock()
        mock_parser.get_page_count.return_value = 1
        mock_image = Image.new('RGB', (100, 100))
        mock_parser.extract_pages.return_value = [
            PageImage(page_number=1, image=mock_image, width=100, height=100, dpi=300)
        ]
        mock_parser_class.return_value = mock_parser
        
        mock_ocr = Mock()
        mock_ocr.extract_text.return_value = OCRResult(text="Test", words=[], confidence=0.95)
        mock_ocr_class.return_value = mock_ocr
        
        mock_layout = Mock()
        mock_layout.analyze.return_value = DocumentStructure(elements=[])
        mock_layout_class.return_value = mock_layout
        
        mock_word_gen = Mock()
        mock_doc = Mock()
        mock_word_gen.create_document.return_value = mock_doc
        mock_word_gen.save.return_value = True
        mock_word_gen_class.return_value = mock_word_gen
        
        # Convert without specifying output path
        converter = PDFConverter()
        result = converter.convert(pdf_path)
        
        assert result["success"] is True
        assert result["output_path"] == expected_output
