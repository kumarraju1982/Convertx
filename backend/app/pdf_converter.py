"""
PDF Converter orchestrator for coordinating the conversion pipeline.

This module coordinates all components to convert PDF files to Word documents.
Uses pdf2docx for direct conversion (preserves structure) and falls back to OCR for scanned pages.
"""

from typing import List, Callable, Optional, Dict, Any
import os
import logging
import fitz  # PyMuPDF
from pdf2docx import Converter
from app.document_parser import DocumentParser
from app.ocr_engine import OCREngine
from app.layout_analyzer import LayoutAnalyzer
from app.word_generator import WordGenerator
from app.text_processor import TextProcessor
from app.models import DocumentStructure, StructureElement, OCRResult, WordBox
from app.exceptions import (
    ConversionError,
    PDFValidationError,
    OCRProcessingError,
    WordGenerationError,
    FileIOError
)

logger = logging.getLogger(__name__)


class PDFConverter:
    """
    Main orchestrator for PDF to Word conversion.
    
    Uses a hybrid approach:
    1. First tries pdf2docx for direct conversion (best quality, preserves structure)
    2. Falls back to OCR pipeline for scanned pages if needed
    """
    
    def __init__(self, ocr_engine: str = None):
            """
            Initialize the PDF converter with all pipeline components.

            Args:
                ocr_engine: OCR engine to use ('tesseract' or 'surya').
                           If None, uses value from config.
            """
            from app.config import Config

            self.parser = DocumentParser()

            # Select OCR engine based on configuration
            if ocr_engine is None:
                ocr_engine = Config.validate_ocr_engine()

            if ocr_engine == 'surya':
                from app.surya_ocr_engine import SuryaOCREngine
                self.ocr_engine = SuryaOCREngine()
                logger.info("Using Surya OCR engine (high accuracy mode)")
            else:  # Default to tesseract
                from app.ocr_engine import OCREngine
                self.ocr_engine = OCREngine()
                logger.info("Using Tesseract OCR engine (fast mode)")

            self.layout_analyzer = LayoutAnalyzer()
            self.word_generator = WordGenerator()
            self.text_processor = TextProcessor()

    
    def validate_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        Validate that the PDF file exists and is valid.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary with validation result:
            {
                "valid": bool,
                "error": str | None,
                "page_count": int | None
            }
            
        Requirements:
            - 1.1: Validate that file exists and is valid PDF format
        """
        result = {
            "valid": False,
            "error": None,
            "page_count": None
        }
        
        # Check if file exists
        if not os.path.exists(pdf_path):
            result["error"] = f"PDF file not found: {pdf_path}"
            return result
        
        # Check if file is readable
        if not os.access(pdf_path, os.R_OK):
            result["error"] = f"PDF file is not readable: {pdf_path}"
            return result
        
        try:
            # Try to get page count (validates PDF format)
            page_count = self.parser.get_page_count(pdf_path)
            
            if page_count == 0:
                result["error"] = "PDF file is empty (contains no pages)"
                return result
            
            result["valid"] = True
            result["page_count"] = page_count
            return result
            
        except Exception as e:
            result["error"] = f"Invalid or corrupted PDF file: {str(e)}"
            return result
    
    def _convert_with_pymupdf_text_extraction(
        self,
        pdf_path: str,
        output_path: str,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> bool:
        """
        Convert PDF using PyMuPDF's text extraction with layout preservation.
        
        This method extracts text with proper spacing and formatting,
        then creates a Word document preserving the structure.
        
        Args:
            pdf_path: Path to input PDF
            output_path: Path for output Word file
            progress_callback: Optional progress callback
            
        Returns:
            True if successful, False otherwise
        """
        try:
            from docx import Document
            from docx.shared import Pt, Inches
            from docx.enum.text import WD_ALIGN_PARAGRAPH
            
            # Open PDF
            doc = fitz.open(pdf_path)
            total_pages = len(doc)
            
            # Create Word document
            word_doc = Document()
            
            # Process each page
            for page_num in range(total_pages):
                if progress_callback:
                    progress_callback(page_num + 1, total_pages)
                
                page = doc[page_num]
                
                # Extract text with layout preservation
                # Use "dict" mode to get detailed layout information
                text_dict = page.get_text("dict")
                
                # Process blocks (paragraphs)
                for block in text_dict["blocks"]:
                    if block["type"] == 0:  # Text block
                        # Extract text from all lines in the block
                        block_text = ""
                        for line in block.get("lines", []):
                            line_text = ""
                            for span in line.get("spans", []):
                                line_text += span.get("text", "")
                            if line_text.strip():
                                block_text += line_text + "\n"
                        
                        if block_text.strip():
                            # Add paragraph to Word document
                            para = word_doc.add_paragraph(block_text.strip())
                            
                            # Try to preserve some formatting
                            if block.get("lines"):
                                first_span = block["lines"][0].get("spans", [{}])[0]
                                font_size = first_span.get("size", 12)
                                
                                # Set font size
                                for run in para.runs:
                                    run.font.size = Pt(font_size)
                                
                                # Detect headings (larger font)
                                if font_size > 14:
                                    para.style = 'Heading 2'
                                elif font_size > 12:
                                    para.style = 'Heading 3'
                
                # Add page break after each page (except last)
                if page_num < total_pages - 1:
                    word_doc.add_page_break()
            
            # Close PDF
            doc.close()
            
            # Save Word document
            word_doc.save(output_path)
            
            # Final progress
            if progress_callback:
                progress_callback(total_pages, total_pages)
            
            return os.path.exists(output_path) and os.path.getsize(output_path) > 0
            
        except Exception as e:
            print(f"PyMuPDF text extraction failed: {e}")
            return False
    
    def _convert_with_pdf2docx(
        self,
        pdf_path: str,
        output_path: str,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> bool:
        """
        Try to convert PDF using pdf2docx library with progress updates.
        
        Args:
            pdf_path: Path to input PDF
            output_path: Path for output Word file
            progress_callback: Optional progress callback
            
        Returns:
            True if successful, False if should fall back to OCR
        """
        import threading
        import time
        
        try:
            # Create converter
            cv = Converter(pdf_path)
            
            # Get page count for progress tracking
            doc = fitz.open(pdf_path)
            total_pages = len(doc)
            doc.close()
            
            # Flag to control progress thread
            conversion_complete = threading.Event()
            
            # Start a background thread to simulate progress updates
            def update_progress():
                current = 0
                while not conversion_complete.is_set() and current < total_pages:
                    current = min(current + 1, total_pages - 1)
                    if progress_callback:
                        try:
                            progress_callback(current, total_pages)
                        except:
                            pass
                    time.sleep(0.5)  # Update every 0.5 seconds
            
            # Start progress thread
            progress_thread = threading.Thread(target=update_progress, daemon=True)
            progress_thread.start()
            
            # Perform conversion
            cv.convert(output_path, start=0, end=None)
            cv.close()
            
            # Signal completion
            conversion_complete.set()
            
            # Post-process to fix spacing issues
            try:
                self.text_processor.fix_word_document(output_path)
            except Exception as e:
                print(f"Warning: Post-processing failed: {e}")
                # Continue anyway - better to have document with spacing issues
            
            # Final progress update
            if progress_callback:
                try:
                    progress_callback(total_pages, total_pages)
                except:
                    pass
            
            # Check if output file was created and has content
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                return True
            
            return False
            
        except Exception as e:
            # If pdf2docx fails, we'll fall back to OCR
            print(f"pdf2docx conversion failed: {e}")
            return False
    
    def convert(
        self,
        pdf_path: str,
        output_path: Optional[str] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Dict[str, Any]:
        """
        Convert a PDF file to a Word document.
        
        Strategy:
        1. Try pdf2docx first (fast, preserves structure perfectly)
        2. If that fails or produces poor results, fall back to OCR pipeline
        
        Args:
            pdf_path: Path to input PDF file
            output_path: Path for output Word file (optional, defaults to same dir as PDF)
            progress_callback: Optional callback function(current_page, total_pages)
            
        Returns:
            Dictionary with conversion result:
            {
                "success": bool,
                "output_path": str | None,
                "pages_processed": int,
                "pages_failed": List[int],
                "errors": List[str]
            }
            
        Requirements:
            - 1.1: Validate PDF file
            - 5.1: Process all pages sequentially
            - 5.3: Continue processing on page failures
            - 6.1: Comprehensive error handling
        """
        errors = []
        pages_failed = []
        
        # Validate PDF
        validation = self.validate_pdf(pdf_path)
        if not validation["valid"]:
            raise PDFValidationError(validation["error"])
        
        total_pages = validation["page_count"]
        
        # Determine output path
        if output_path is None:
            # Use same directory as input, change extension to .docx
            base = os.path.splitext(pdf_path)[0]
            output_path = f"{base}.docx"
        
        # Try PyMuPDF text extraction first (best for text-based PDFs)
        try:
            if self._convert_with_pymupdf_text_extraction(pdf_path, output_path, progress_callback):
                # Success! Return result
                return {
                    "success": True,
                    "output_path": output_path,
                    "pages_processed": total_pages,
                    "pages_failed": [],
                    "errors": []
                }
        except Exception as e:
            # Log error and try next method
            errors.append(f"PyMuPDF text extraction failed: {str(e)}, trying pdf2docx")
        
        # Try pdf2docx as fallback (preserves structure but may have spacing issues)
        try:
            if self._convert_with_pdf2docx(pdf_path, output_path, progress_callback):
                # Success! Return result
                return {
                    "success": True,
                    "output_path": output_path,
                    "pages_processed": total_pages,
                    "pages_failed": [],
                    "errors": errors if errors else []
                }
        except Exception as e:
            # Log error and fall back to OCR
            errors.append(f"pdf2docx conversion failed: {str(e)}, falling back to OCR")
        
        # Fall back to OCR pipeline for scanned documents
        try:
            # Open PDF document
            doc = fitz.open(pdf_path)
            
            # Process each page through the OCR pipeline
            document_structures = []
            
            for page_idx in range(len(doc)):
                page_number = page_idx + 1
                
                try:
                    # Update progress
                    if progress_callback:
                        progress_callback(page_number, total_pages)
                    
                    page = doc[page_idx]
                    
                    # Extract page as image for OCR
                    page_images = self.parser.extract_pages(pdf_path)
                    page_image = page_images[page_idx]
                    
                    # Perform OCR
                    ocr_result = self.ocr_engine.extract_text(page_image.image)
                    
                    # Analyze layout
                    structure = self.layout_analyzer.analyze(ocr_result)
                    
                    document_structures.append(structure)
                    
                except OCRProcessingError as e:
                    # Log OCR error and continue
                    error_msg = f"Page {page_number}: OCR failed - {str(e)}"
                    errors.append(error_msg)
                    pages_failed.append(page_number)
                    # Add empty structure for failed page
                    document_structures.append(DocumentStructure(elements=[]))
                    
                except Exception as e:
                    # Log unexpected error and continue
                    error_msg = f"Page {page_number}: Processing failed - {str(e)}"
                    errors.append(error_msg)
                    pages_failed.append(page_number)
                    # Add empty structure for failed page
                    document_structures.append(DocumentStructure(elements=[]))
            
            # Close PDF document
            doc.close()
            
            # Generate Word document from all structures
            try:
                word_doc = self.word_generator.create_document(document_structures)
                self.word_generator.save(word_doc, output_path)
                
            except Exception as e:
                raise WordGenerationError(f"Failed to generate Word document: {str(e)}")
            
            # Return success result
            return {
                "success": True,
                "output_path": output_path,
                "pages_processed": total_pages - len(pages_failed),
                "pages_failed": pages_failed,
                "errors": errors
            }
            
        except PDFValidationError:
            # Re-raise validation errors
            raise
        except WordGenerationError:
            # Re-raise Word generation errors
            raise
        except Exception as e:
            # Wrap unexpected errors
            raise ConversionError(f"Conversion failed: {str(e)}")
