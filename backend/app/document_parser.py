"""
Document Parser component for PDF page extraction.

This module handles PDF file validation and extraction of pages as images
suitable for OCR processing.
"""

import os
import io
from typing import List
import fitz  # PyMuPDF
from PIL import Image

from .models import PageImage
from .exceptions import PDFValidationError, FileIOError


class DocumentParser:
    """
    Handles PDF file parsing and page extraction.
    
    This class is responsible for:
    - Validating PDF files
    - Extracting pages as PIL images
    - Maintaining page order
    - Handling PDF-related errors
    """
    
    def __init__(self, dpi: int = 300):
        """
        Initialize the DocumentParser.
        
        Args:
            dpi: Resolution for page extraction (default: 300 DPI)
        """
        self.dpi = dpi
    
    def get_page_count(self, pdf_path: str) -> int:
        """
        Get the number of pages in a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Number of pages in the PDF
            
        Raises:
            FileIOError: If the file doesn't exist or cannot be accessed
            PDFValidationError: If the file is not a valid PDF or is corrupted
        """
        # Validate file exists
        if not os.path.exists(pdf_path):
            raise FileIOError(
                f"PDF file not found: {pdf_path}",
                details={"path": pdf_path}
            )
        
        # Validate file is readable
        if not os.path.isfile(pdf_path):
            raise FileIOError(
                f"Path is not a file: {pdf_path}",
                details={"path": pdf_path}
            )
        
        try:
            # Open PDF and get page count
            doc = fitz.open(pdf_path)
            page_count = len(doc)
            doc.close()
            
            # Validate PDF is not empty
            if page_count == 0:
                raise PDFValidationError(
                    "PDF file contains no pages",
                    details={"path": pdf_path}
                )
            
            return page_count
            
        except fitz.FileDataError as e:
            raise PDFValidationError(
                f"Invalid or corrupted PDF file: {str(e)}",
                details={"path": pdf_path, "error": str(e)}
            )
        except Exception as e:
            raise PDFValidationError(
                f"Failed to read PDF file: {str(e)}",
                details={"path": pdf_path, "error": str(e)}
            )
    
    def extract_pages(self, pdf_path: str) -> List[PageImage]:
        """
        Extract all pages from a PDF as images.
        
        This method converts each page of the PDF to a PIL Image object
        at the specified DPI resolution. Pages are returned in their
        original order.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            List of PageImage objects, one per page in order
            
        Raises:
            FileIOError: If the file doesn't exist or cannot be accessed
            PDFValidationError: If the file is not a valid PDF or is corrupted
        """
        # Validate file exists
        if not os.path.exists(pdf_path):
            raise FileIOError(
                f"PDF file not found: {pdf_path}",
                details={"path": pdf_path}
            )
        
        # Validate file is readable
        if not os.path.isfile(pdf_path):
            raise FileIOError(
                f"Path is not a file: {pdf_path}",
                details={"path": pdf_path}
            )
        
        try:
            # Open PDF document
            doc = fitz.open(pdf_path)
            
            # Validate PDF is not empty
            if len(doc) == 0:
                doc.close()
                raise PDFValidationError(
                    "PDF file contains no pages",
                    details={"path": pdf_path}
                )
            
            pages = []
            
            # Calculate zoom factor for desired DPI
            # PyMuPDF default is 72 DPI, so zoom = target_dpi / 72
            zoom = self.dpi / 72.0
            mat = fitz.Matrix(zoom, zoom)
            
            # Extract each page in order
            for page_num in range(len(doc)):
                try:
                    # Get page
                    page = doc[page_num]
                    
                    # Render page to pixmap at specified DPI
                    pix = page.get_pixmap(matrix=mat)
                    
                    # Convert pixmap to PIL Image
                    # PyMuPDF pixmap is in RGB format
                    img_data = pix.tobytes("ppm")
                    image = Image.open(io.BytesIO(img_data))
                    
                    # Create PageImage object
                    page_image = PageImage(
                        page_number=page_num + 1,  # 1-indexed for user-facing
                        image=image,
                        width=pix.width,
                        height=pix.height,
                        dpi=self.dpi
                    )
                    
                    pages.append(page_image)
                    
                except Exception as e:
                    # Close document before re-raising
                    doc.close()
                    raise PDFValidationError(
                        f"Failed to extract page {page_num + 1}: {str(e)}",
                        details={
                            "path": pdf_path,
                            "page_number": page_num + 1,
                            "error": str(e)
                        }
                    )
            
            # Close document
            doc.close()
            
            return pages
            
        except fitz.FileDataError as e:
            raise PDFValidationError(
                f"Invalid or corrupted PDF file: {str(e)}",
                details={"path": pdf_path, "error": str(e)}
            )
        except PDFValidationError:
            # Re-raise our own exceptions
            raise
        except Exception as e:
            raise PDFValidationError(
                f"Failed to read PDF file: {str(e)}",
                details={"path": pdf_path, "error": str(e)}
            )
