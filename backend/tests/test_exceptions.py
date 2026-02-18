"""
Unit tests for custom exception hierarchy.
"""

import pytest
from app.exceptions import (
    ConversionError,
    PDFValidationError,
    OCRProcessingError,
    WordGenerationError,
    FileIOError,
    JobNotFoundError,
    FileUploadError,
)


class TestConversionError:
    """Tests for the base ConversionError class."""
    
    def test_basic_initialization(self):
        """Test basic error initialization with message only."""
        error = ConversionError("Test error message")
        assert str(error) == "Test error message"
        assert error.message == "Test error message"
        assert error.details == {}
    
    def test_initialization_with_details(self):
        """Test error initialization with additional details."""
        details = {"file": "test.pdf", "page": 5}
        error = ConversionError("Test error", details=details)
        assert error.message == "Test error"
        assert error.details == details
        assert error.details["file"] == "test.pdf"
        assert error.details["page"] == 5
    
    def test_is_exception(self):
        """Test that ConversionError is an Exception."""
        error = ConversionError("Test")
        assert isinstance(error, Exception)


class TestPDFValidationError:
    """Tests for PDFValidationError."""
    
    def test_inheritance(self):
        """Test that PDFValidationError inherits from ConversionError."""
        error = PDFValidationError("Invalid PDF")
        assert isinstance(error, ConversionError)
        assert isinstance(error, Exception)
    
    def test_message_and_details(self):
        """Test PDFValidationError with message and details."""
        details = {"path": "/invalid/file.pdf", "reason": "corrupted"}
        error = PDFValidationError("PDF validation failed", details=details)
        assert error.message == "PDF validation failed"
        assert error.details["path"] == "/invalid/file.pdf"


class TestOCRProcessingError:
    """Tests for OCRProcessingError."""
    
    def test_inheritance(self):
        """Test that OCRProcessingError inherits from ConversionError."""
        error = OCRProcessingError("OCR failed")
        assert isinstance(error, ConversionError)
        assert isinstance(error, Exception)
    
    def test_message_and_details(self):
        """Test OCRProcessingError with message and details."""
        details = {"page": 3, "image_format": "unsupported"}
        error = OCRProcessingError("OCR processing failed", details=details)
        assert error.message == "OCR processing failed"
        assert error.details["page"] == 3


class TestWordGenerationError:
    """Tests for WordGenerationError."""
    
    def test_inheritance(self):
        """Test that WordGenerationError inherits from ConversionError."""
        error = WordGenerationError("Word generation failed")
        assert isinstance(error, ConversionError)
        assert isinstance(error, Exception)
    
    def test_message_and_details(self):
        """Test WordGenerationError with message and details."""
        details = {"output_path": "/invalid/output.docx"}
        error = WordGenerationError("Failed to save document", details=details)
        assert error.message == "Failed to save document"
        assert error.details["output_path"] == "/invalid/output.docx"


class TestFileIOError:
    """Tests for FileIOError."""
    
    def test_inheritance(self):
        """Test that FileIOError inherits from ConversionError."""
        error = FileIOError("File I/O failed")
        assert isinstance(error, ConversionError)
        assert isinstance(error, Exception)
    
    def test_message_and_details(self):
        """Test FileIOError with message and details."""
        details = {"operation": "read", "path": "/missing/file.pdf"}
        error = FileIOError("Cannot read file", details=details)
        assert error.message == "Cannot read file"
        assert error.details["operation"] == "read"


class TestJobNotFoundError:
    """Tests for JobNotFoundError."""
    
    def test_inheritance(self):
        """Test that JobNotFoundError inherits from ConversionError."""
        error = JobNotFoundError("Job not found")
        assert isinstance(error, ConversionError)
        assert isinstance(error, Exception)
    
    def test_message_and_details(self):
        """Test JobNotFoundError with message and details."""
        details = {"job_id": "abc123"}
        error = JobNotFoundError("Job does not exist", details=details)
        assert error.message == "Job does not exist"
        assert error.details["job_id"] == "abc123"


class TestFileUploadError:
    """Tests for FileUploadError."""
    
    def test_inheritance(self):
        """Test that FileUploadError inherits from ConversionError."""
        error = FileUploadError("Upload failed")
        assert isinstance(error, ConversionError)
        assert isinstance(error, Exception)
    
    def test_message_and_details(self):
        """Test FileUploadError with message and details."""
        details = {"file_type": "image/png", "max_size": 52428800}
        error = FileUploadError("Invalid file type", details=details)
        assert error.message == "Invalid file type"
        assert error.details["file_type"] == "image/png"


class TestExceptionHierarchy:
    """Tests for the overall exception hierarchy."""
    
    def test_all_exceptions_inherit_from_conversion_error(self):
        """Test that all custom exceptions inherit from ConversionError."""
        exceptions = [
            PDFValidationError("test"),
            OCRProcessingError("test"),
            WordGenerationError("test"),
            FileIOError("test"),
            JobNotFoundError("test"),
            FileUploadError("test"),
        ]
        
        for exc in exceptions:
            assert isinstance(exc, ConversionError)
            assert isinstance(exc, Exception)
    
    def test_exception_catching_by_base_class(self):
        """Test that specific exceptions can be caught by base class."""
        try:
            raise PDFValidationError("Test error")
        except ConversionError as e:
            assert e.message == "Test error"
        
        try:
            raise JobNotFoundError("Job missing")
        except ConversionError as e:
            assert e.message == "Job missing"
    
    def test_exception_catching_by_specific_type(self):
        """Test that exceptions can be caught by their specific type."""
        with pytest.raises(PDFValidationError):
            raise PDFValidationError("Invalid PDF")
        
        with pytest.raises(OCRProcessingError):
            raise OCRProcessingError("OCR failed")
        
        with pytest.raises(WordGenerationError):
            raise WordGenerationError("Word generation failed")
