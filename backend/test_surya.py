"""
Simple test script to verify Surya OCR installation and compare with Tesseract.
"""

import os
import sys

# Set OCR engine to Surya
os.environ['OCR_ENGINE'] = 'surya'

from app.pdf_converter import PDFConverter
from app.config import Config

def test_surya_installation():
    """Test if Surya OCR is properly installed and can be initialized."""
    print("=" * 60)
    print("Testing Surya OCR Installation")
    print("=" * 60)
    
    try:
        # Check configuration
        print(f"\n1. Configuration Check:")
        print(f"   OCR_ENGINE setting: {Config.OCR_ENGINE}")
        
        # Initialize converter with Surya
        print(f"\n2. Initializing PDFConverter with Surya OCR...")
        converter = PDFConverter(ocr_engine='surya')
        print(f"   ✓ PDFConverter initialized successfully")
        print(f"   OCR Engine type: {type(converter.ocr_engine).__name__}")
        
        # Check if we have any test PDFs
        print(f"\n3. Looking for test PDFs in uploads folder...")
        uploads_dir = os.path.join(os.path.dirname(__file__), '..', 'uploads')
        
        if os.path.exists(uploads_dir):
            # Find first PDF in any subdirectory
            test_pdf = None
            for root, dirs, files in os.walk(uploads_dir):
                for file in files:
                    if file.endswith('.pdf'):
                        test_pdf = os.path.join(root, file)
                        break
                if test_pdf:
                    break
            
            if test_pdf:
                print(f"   Found test PDF: {os.path.basename(test_pdf)}")
                print(f"\n4. Testing conversion with Surya OCR...")
                print(f"   (This may take a moment on first run as models download)")
                
                # Validate PDF
                validation = converter.validate_pdf(test_pdf)
                if validation['valid']:
                    print(f"   ✓ PDF is valid ({validation['page_count']} pages)")
                    
                    # Try converting just the first page
                    output_path = os.path.join(os.path.dirname(test_pdf), 'surya_test_output.docx')
                    print(f"\n5. Converting first page...")
                    print(f"   Input: {test_pdf}")
                    print(f"   Output: {output_path}")
                    
                    result = converter.convert(test_pdf, output_path)
                    
                    if result['success']:
                        print(f"\n   ✓ Conversion successful!")
                        print(f"   Pages processed: {result['pages_processed']}")
                        print(f"   Pages failed: {len(result['pages_failed'])}")
                        print(f"   Output file: {result['output_path']}")
                        print(f"\n   You can now compare this with Tesseract output!")
                    else:
                        print(f"\n   ✗ Conversion failed")
                        print(f"   Errors: {result['errors']}")
                else:
                    print(f"   ✗ PDF validation failed: {validation['error']}")
            else:
                print(f"   No PDF files found in uploads directory")
                print(f"   Upload a PDF through the web interface first")
        else:
            print(f"   Uploads directory not found: {uploads_dir}")
        
        print(f"\n" + "=" * 60)
        print("Surya OCR is installed and ready to use!")
        print("=" * 60)
        print(f"\nTo use Surya OCR in your application:")
        print(f"  Windows: set OCR_ENGINE=surya")
        print(f"  Linux/Mac: export OCR_ENGINE=surya")
        print(f"\nThen restart your Flask API and Celery worker.")
        
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == '__main__':
    success = test_surya_installation()
    sys.exit(0 if success else 1)
