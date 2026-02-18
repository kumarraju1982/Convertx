"""
Custom exception hierarchy for PDF to Word converter.

This module defines all custom exceptions used throughout the application
for error handling and reporting.
"""


class ConversionError(Exception):
    """Base exception for all conversion-related errors."""
    
    def __init__(self, message: str, details: dict = None):
        """
        Initialize conversion error.
        
        Args:
            message: Human-readable error message
            details: Optional dictionary with additional error context
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}


class PDFValidationError(ConversionError):
    """Raised when a PDF file is invalid, corrupted, or cannot be processed."""
    pass


class OCRProcessingError(ConversionError):
    """Raised when OCR processing fails on an image."""
    pass


class WordGenerationError(ConversionError):
    """Raised when Word document generation or saving fails."""
    pass


class FileIOError(ConversionError):
    """Raised when file input/output operations fail."""
    pass


class JobNotFoundError(ConversionError):
    """Raised when a requested job ID does not exist."""
    pass


class FileUploadError(ConversionError):
    """Raised when file upload validation fails."""
    pass
