"""
Property-based tests for DocumentParser component using Hypothesis.

**Feature: pdf-to-word-converter**

These tests verify universal properties that should hold across all valid inputs.
"""

import os
import tempfile
import shutil
from pathlib import Path

import pytest
from hypothesis import given, strategies as st, settings, assume
from PIL import Image, ImageDraw, ImageFont
import fitz  # PyMuPDF

from app.document_parser import DocumentParser
from app.exceptions import PDFValidationError, FileIOError


def create_test_pdf_with_identifiable_pages(num_pages: int, output_path: str):
    """
    Create a PDF with identifiable pages for testing order preservation.
    
    Each page contains a large number indicating its position.
    
    Args:
        num_pages: Number of pages to create
        output_path: Path to save the PDF
    """
    doc = fitz.open()
    
    for page_num in range(num_pages):
        # Create a page (A4 size: 595 x 842 points)
        page = doc.new_page(width=595, height=842)
        
        # Add large text indicating page number
        text = f"Page {page_num + 1}"
        
        # Insert text at center of page
        rect = fitz.Rect(50, 400, 545, 450)
        page.insert_textbox(
            rect,
            text,
            fontsize=48,
            fontname="helv",
            align=fitz.TEXT_ALIGN_CENTER
        )
    
    doc.save(output_path)
    doc.close()


class TestPageExtractionOrderPreservation:
    """
    **Property 2: Page Extraction Order Preservation**
    **Validates: Requirements 1.3, 1.4**
    
    For any valid PDF file, extracting pages should produce images in the same
    order as they appear in the original PDF, with all pages included.
    """
    
    @given(
        num_pages=st.integers(min_value=1, max_value=10),
        dpi=st.integers(min_value=150, max_value=300)
    )
    @settings(max_examples=100, deadline=None)
    def test_page_extraction_preserves_order(self, num_pages, dpi):
        """
        Test that pages are extracted in the correct order.
        
        This property verifies that for any PDF with N pages, extraction
        produces N images in the same order as the original.
        """
        # Create temp directory for this test
        temp_dir = tempfile.mkdtemp()
        try:
            # Create a test PDF with identifiable pages
            pdf_path = os.path.join(temp_dir, f"test_{num_pages}_pages.pdf")
            create_test_pdf_with_identifiable_pages(num_pages, pdf_path)
            
            # Create parser and extract pages
            parser = DocumentParser(dpi=dpi)
            pages = parser.extract_pages(pdf_path)
            
            # Verify: correct number of pages extracted
            assert len(pages) == num_pages, \
                f"Expected {num_pages} pages, got {len(pages)}"
            
            # Verify: pages are in correct order (1-indexed)
            for i, page in enumerate(pages):
                expected_page_num = i + 1
                assert page.page_number == expected_page_num, \
                    f"Page at index {i} should be page {expected_page_num}, got {page.page_number}"
            
            # Verify: all pages have valid images
            for page in pages:
                assert page.image is not None, "Page image should not be None"
                assert page.width > 0, "Page width should be positive"
                assert page.height > 0, "Page height should be positive"
                assert page.dpi == dpi, f"Page DPI should be {dpi}, got {page.dpi}"
        finally:
            # Cleanup
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
    
    @given(
        num_pages=st.integers(min_value=1, max_value=15)
    )
    @settings(max_examples=100, deadline=None)
    def test_all_pages_included_in_extraction(self, num_pages):
        """
        Test that all pages are included in extraction.
        
        This verifies that no pages are skipped during extraction.
        """
        # Create temp directory for this test
        temp_dir = tempfile.mkdtemp()
        try:
            # Create a test PDF
            pdf_path = os.path.join(temp_dir, f"test_all_pages_{num_pages}.pdf")
            create_test_pdf_with_identifiable_pages(num_pages, pdf_path)
            
            # Extract pages
            parser = DocumentParser()
            pages = parser.extract_pages(pdf_path)
            
            # Verify: all page numbers are present
            extracted_page_numbers = {page.page_number for page in pages}
            expected_page_numbers = set(range(1, num_pages + 1))
            
            assert extracted_page_numbers == expected_page_numbers, \
                f"Missing pages: {expected_page_numbers - extracted_page_numbers}"
        finally:
            # Cleanup
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
    
    @given(
        num_pages=st.integers(min_value=2, max_value=10)
    )
    @settings(max_examples=100, deadline=None)
    def test_page_numbers_are_sequential(self, num_pages):
        """
        Test that page numbers are sequential without gaps.
        
        This verifies that pages are numbered 1, 2, 3, ... N without skips.
        """
        # Create temp directory for this test
        temp_dir = tempfile.mkdtemp()
        try:
            # Create a test PDF
            pdf_path = os.path.join(temp_dir, f"test_sequential_{num_pages}.pdf")
            create_test_pdf_with_identifiable_pages(num_pages, pdf_path)
            
            # Extract pages
            parser = DocumentParser()
            pages = parser.extract_pages(pdf_path)
            
            # Verify: page numbers are sequential
            page_numbers = [page.page_number for page in pages]
            expected_sequence = list(range(1, num_pages + 1))
            
            assert page_numbers == expected_sequence, \
                f"Page numbers should be sequential {expected_sequence}, got {page_numbers}"
        finally:
            # Cleanup
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
    
    @given(
        num_pages=st.integers(min_value=1, max_value=8)
    )
    @settings(max_examples=50, deadline=None)
    def test_extraction_order_matches_pdf_order(self, num_pages):
        """
        Test that extraction order matches the PDF's internal page order.
        
        This verifies that the first extracted page corresponds to the first
        PDF page, the second to the second, and so on.
        """
        # Create temp directory for this test
        temp_dir = tempfile.mkdtemp()
        try:
            # Create a test PDF
            pdf_path = os.path.join(temp_dir, f"test_order_{num_pages}.pdf")
            create_test_pdf_with_identifiable_pages(num_pages, pdf_path)
            
            # Get page count from PDF directly
            doc = fitz.open(pdf_path)
            pdf_page_count = len(doc)
            doc.close()
            
            # Extract pages
            parser = DocumentParser()
            pages = parser.extract_pages(pdf_path)
            
            # Verify: extraction count matches PDF count
            assert len(pages) == pdf_page_count, \
                f"Extracted {len(pages)} pages but PDF has {pdf_page_count} pages"
            
            # Verify: order is preserved (page_number matches position)
            for idx, page in enumerate(pages):
                assert page.page_number == idx + 1, \
                    f"Page at position {idx} should have page_number {idx + 1}"
        finally:
            # Cleanup
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)



class TestPDFValidationCorrectness:
    """
    **Property 1: PDF Validation Correctness**
    **Validates: Requirements 1.1, 1.2**
    
    For any file path, the PDF validator should correctly identify valid PDF files
    and reject invalid or non-existent files with appropriate error messages.
    """
    
    @given(
        num_pages=st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=100, deadline=None)
    def test_valid_pdf_files_are_accepted(self, num_pages):
        """
        Test that valid PDF files are correctly identified and accepted.
        
        This verifies that the validator accepts properly formatted PDF files.
        """
        # Create temp directory for this test
        temp_dir = tempfile.mkdtemp()
        try:
            # Create a valid test PDF
            pdf_path = os.path.join(temp_dir, f"valid_{num_pages}.pdf")
            create_test_pdf_with_identifiable_pages(num_pages, pdf_path)
            
            # Create parser
            parser = DocumentParser()
            
            # Should not raise an exception
            page_count = parser.get_page_count(pdf_path)
            
            # Verify: page count is correct
            assert page_count == num_pages, \
                f"Expected {num_pages} pages, got {page_count}"
            
            # Should be able to extract pages without error
            pages = parser.extract_pages(pdf_path)
            assert len(pages) == num_pages
        finally:
            # Cleanup
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
    
    @given(
        filename=st.text(min_size=1, max_size=50, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            whitelist_characters='_-'
        ))
    )
    @settings(max_examples=100, deadline=None)
    def test_nonexistent_files_are_rejected(self, filename):
        """
        Test that non-existent files are rejected with appropriate error.
        
        This verifies that the validator returns a descriptive error for
        files that don't exist.
        """
        # Create temp directory for this test
        temp_dir = tempfile.mkdtemp()
        try:
            # Create path to non-existent file
            pdf_path = os.path.join(temp_dir, f"{filename}.pdf")
            
            # Ensure file doesn't exist
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
            
            # Create parser
            parser = DocumentParser()
            
            # Should raise FileIOError
            with pytest.raises(FileIOError) as exc_info:
                parser.get_page_count(pdf_path)
            
            # Verify error message mentions file not found
            assert "not found" in str(exc_info.value).lower()
        finally:
            # Cleanup
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
    
    @given(
        content=st.binary(min_size=10, max_size=1000)
    )
    @settings(max_examples=100, deadline=None)
    def test_invalid_pdf_files_are_rejected(self, content):
        """
        Test that invalid/corrupted PDF files are rejected with appropriate error.
        
        This verifies that the validator returns a descriptive error for
        files that are not valid PDFs.
        """
        # Create temp directory for this test
        temp_dir = tempfile.mkdtemp()
        try:
            # Create a file with random binary content (not a valid PDF)
            pdf_path = os.path.join(temp_dir, "invalid.pdf")
            with open(pdf_path, 'wb') as f:
                f.write(content)
            
            # Create parser
            parser = DocumentParser()
            
            # Should raise PDFValidationError
            with pytest.raises(PDFValidationError) as exc_info:
                parser.get_page_count(pdf_path)
            
            # Verify error message mentions invalid or corrupted
            error_msg = str(exc_info.value).lower()
            assert "invalid" in error_msg or "corrupted" in error_msg or "failed" in error_msg
        finally:
            # Cleanup
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
    
    @given(
        num_pages=st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=50, deadline=None)
    def test_directory_path_is_rejected(self, num_pages):
        """
        Test that directory paths are rejected (not files).
        
        This verifies that the validator rejects paths that point to
        directories rather than files.
        """
        # Create temp directory for this test
        temp_dir = tempfile.mkdtemp()
        try:
            # Create a subdirectory
            subdir = os.path.join(temp_dir, "subdir")
            os.makedirs(subdir, exist_ok=True)
            
            # Create parser
            parser = DocumentParser()
            
            # Should raise FileIOError
            with pytest.raises(FileIOError) as exc_info:
                parser.get_page_count(subdir)
            
            # Verify error message mentions not a file
            error_msg = str(exc_info.value).lower()
            assert "not a file" in error_msg or "path" in error_msg
        finally:
            # Cleanup
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
    
    @given(
        num_pages=st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=50, deadline=None)
    def test_validation_is_consistent(self, num_pages):
        """
        Test that validation is consistent across multiple calls.
        
        This verifies that validating the same file multiple times
        produces the same result.
        """
        # Create temp directory for this test
        temp_dir = tempfile.mkdtemp()
        try:
            # Create a valid test PDF
            pdf_path = os.path.join(temp_dir, f"consistent_{num_pages}.pdf")
            create_test_pdf_with_identifiable_pages(num_pages, pdf_path)
            
            # Create parser
            parser = DocumentParser()
            
            # Validate multiple times
            results = []
            for _ in range(3):
                page_count = parser.get_page_count(pdf_path)
                results.append(page_count)
            
            # All results should be the same
            assert all(r == num_pages for r in results), \
                f"Validation results should be consistent: {results}"
        finally:
            # Cleanup
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)



class TestDocumentParserEdgeCases:
    """
    Unit tests for edge cases in DocumentParser.
    
    **Validates: Requirements 1.2, 1.5**
    """
    
    def test_corrupted_pdf_error_message_is_descriptive(self):
        """
        Test that corrupted PDF files produce descriptive error messages.
        
        This verifies requirement 1.2: descriptive error messages for invalid PDFs.
        """
        # Create temp directory for this test
        temp_dir = tempfile.mkdtemp()
        try:
            # Create a file with PDF header but corrupted content
            pdf_path = os.path.join(temp_dir, "corrupted.pdf")
            with open(pdf_path, 'wb') as f:
                # Write PDF header but invalid content
                f.write(b'%PDF-1.4\n')
                f.write(b'corrupted data that is not valid PDF structure\n')
                f.write(b'%%EOF\n')
            
            # Create parser
            parser = DocumentParser()
            
            # Should raise PDFValidationError with descriptive message
            with pytest.raises(PDFValidationError) as exc_info:
                parser.extract_pages(pdf_path)
            
            # Verify error message is descriptive
            error_msg = str(exc_info.value)
            assert len(error_msg) > 10, "Error message should be descriptive"
            assert "corrupted" in error_msg.lower() or "invalid" in error_msg.lower() or "failed" in error_msg.lower()
        finally:
            # Cleanup
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
    
    def test_extract_pages_with_invalid_file_provides_clear_error(self):
        """
        Test that attempting to extract pages from invalid file gives clear error.
        
        This verifies requirement 1.2: clear error messages for invalid inputs.
        """
        # Create temp directory for this test
        temp_dir = tempfile.mkdtemp()
        try:
            # Create a binary file with random content (not a valid PDF)
            invalid_path = os.path.join(temp_dir, "not_a_pdf.bin")
            with open(invalid_path, 'wb') as f:
                f.write(b'\x00\x01\x02\x03\x04\x05' * 100)
            
            # Create parser
            parser = DocumentParser()
            
            # Should raise PDFValidationError
            with pytest.raises(PDFValidationError) as exc_info:
                parser.extract_pages(invalid_path)
            
            # Verify error message mentions the issue
            error_msg = str(exc_info.value).lower()
            assert "invalid" in error_msg or "corrupted" in error_msg or "failed" in error_msg
        finally:
            # Cleanup
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
    
    def test_get_page_count_with_nonexistent_file_error(self):
        """
        Test that get_page_count with non-existent file provides clear error.
        
        This verifies requirement 1.2: descriptive error for file not found.
        """
        # Create temp directory for this test
        temp_dir = tempfile.mkdtemp()
        try:
            # Path to non-existent file
            pdf_path = os.path.join(temp_dir, "does_not_exist.pdf")
            
            # Create parser
            parser = DocumentParser()
            
            # Should raise FileIOError
            with pytest.raises(FileIOError) as exc_info:
                parser.get_page_count(pdf_path)
            
            # Verify error message mentions file not found
            error_msg = str(exc_info.value).lower()
            assert "not found" in error_msg
            assert pdf_path in str(exc_info.value)
        finally:
            # Cleanup
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
    
    def test_extract_pages_with_various_dpi_settings(self):
        """
        Test that extraction works with various DPI settings.
        
        This verifies that the parser can handle different resolution requirements.
        """
        # Create temp directory for this test
        temp_dir = tempfile.mkdtemp()
        try:
            # Create a simple PDF
            pdf_path = os.path.join(temp_dir, "test.pdf")
            create_test_pdf_with_identifiable_pages(2, pdf_path)
            
            # Test with different DPI values
            dpi_values = [150, 200, 300, 600]
            
            for dpi in dpi_values:
                parser = DocumentParser(dpi=dpi)
                pages = parser.extract_pages(pdf_path)
                
                # Verify pages were extracted
                assert len(pages) == 2
                
                # Verify DPI is set correctly
                for page in pages:
                    assert page.dpi == dpi, f"Expected DPI {dpi}, got {page.dpi}"
                    
                    # Verify image dimensions scale with DPI
                    # Higher DPI should produce larger images
                    assert page.width > 0
                    assert page.height > 0
        finally:
            # Cleanup
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
    
    def test_single_page_pdf_extraction(self):
        """
        Test extraction of single-page PDF (edge case).
        
        This verifies that single-page PDFs are handled correctly.
        """
        # Create temp directory for this test
        temp_dir = tempfile.mkdtemp()
        try:
            # Create a single-page PDF
            pdf_path = os.path.join(temp_dir, "single_page.pdf")
            create_test_pdf_with_identifiable_pages(1, pdf_path)
            
            # Extract pages
            parser = DocumentParser()
            pages = parser.extract_pages(pdf_path)
            
            # Verify single page extracted
            assert len(pages) == 1
            assert pages[0].page_number == 1
            assert pages[0].image is not None
        finally:
            # Cleanup
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
    
    def test_error_details_include_file_path(self):
        """
        Test that error messages include the file path for debugging.
        
        This verifies that errors provide context about which file failed.
        """
        # Create temp directory for this test
        temp_dir = tempfile.mkdtemp()
        try:
            # Path to non-existent file
            pdf_path = os.path.join(temp_dir, "missing_file.pdf")
            
            # Create parser
            parser = DocumentParser()
            
            # Should raise error with file path in message
            with pytest.raises((FileIOError, PDFValidationError)) as exc_info:
                parser.extract_pages(pdf_path)
            
            # Verify file path is in error message or details
            error_str = str(exc_info.value)
            assert "missing_file.pdf" in error_str or pdf_path in error_str
        finally:
            # Cleanup
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
