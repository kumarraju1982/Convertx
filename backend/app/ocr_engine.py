"""
OCR Engine for extracting text from images using Tesseract.

This module provides OCR functionality to extract text content with bounding box
information and confidence scores from page images.
"""

import pytesseract
from PIL import Image
from typing import List
import os
from app.models import OCRResult, WordBox
from app.exceptions import OCRProcessingError

# Configure Tesseract path for Windows
if os.name == 'nt':  # Windows
    tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    if os.path.exists(tesseract_path):
        pytesseract.pytesseract.tesseract_cmd = tesseract_path


class OCREngine:
    """
    OCR Engine that uses Tesseract to extract text from images.
    
    This class provides methods to extract text with word-level bounding boxes
    and confidence scores, supporting requirements 2.1, 2.2, and 2.5.
    """
    
    def __init__(self):
        """Initialize the OCR Engine."""
        pass
    
    def extract_text(self, image: Image.Image) -> OCRResult:
        """
        Extract text from an image with bounding box information and confidence scores.
        
        Uses Tesseract OCR to extract text at word-level granularity, including
        position information and confidence scores for each word. The text is
        extracted in reading order (left-to-right, top-to-bottom).
        
        Args:
            image: PIL Image object to extract text from
            
        Returns:
            OCRResult containing:
                - text: Full extracted text content
                - words: List of WordBox objects with position and confidence
                - confidence: Overall confidence score (0.0 to 1.0)
                
        Raises:
            OCRProcessingError: If OCR processing fails
            
        Requirements:
            - 2.1: Extract all visible text content
            - 2.2: Preserve reading order (left-to-right, top-to-bottom)
            - 2.5: Provide confidence scores for recognized text
        """
        try:
            # Preprocess image for better OCR accuracy
            preprocessed_image = self.preprocess_image(image)
            
            # Custom Tesseract configuration for better accuracy
            # --psm 1: Automatic page segmentation with OSD (Orientation and Script Detection)
            # --oem 3: Default OCR Engine Mode (LSTM + Legacy)
            custom_config = r'--oem 3 --psm 1'
            
            # Extract detailed OCR data with bounding boxes and confidence scores
            # Output format: level, page_num, block_num, par_num, line_num, word_num,
            #                left, top, width, height, conf, text
            ocr_data = pytesseract.image_to_data(
                preprocessed_image,
                output_type=pytesseract.Output.DICT,
                lang='eng',
                config=custom_config
            )
            
            # Extract word-level information
            words: List[WordBox] = []
            confidences: List[float] = []
            
            for i in range(len(ocr_data['text'])):
                text = ocr_data['text'][i].strip()
                conf = float(ocr_data['conf'][i])
                
                # Skip empty text or invalid confidence scores
                if not text or conf < 0:
                    continue
                
                # Create WordBox with position and confidence
                word_box = WordBox(
                    text=text,
                    x=int(ocr_data['left'][i]),
                    y=int(ocr_data['top'][i]),
                    width=int(ocr_data['width'][i]),
                    height=int(ocr_data['height'][i]),
                    confidence=conf / 100.0  # Convert to 0.0-1.0 range
                )
                words.append(word_box)
                confidences.append(word_box.confidence)
            
            # Calculate overall confidence (average of word confidences)
            overall_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            # Extract full text (preserves reading order) with custom config
            full_text = pytesseract.image_to_string(
                preprocessed_image, 
                lang='eng',
                config=custom_config
            ).strip()
            
            return OCRResult(
                text=full_text,
                words=words,
                confidence=overall_confidence
            )
            
        except pytesseract.TesseractNotFoundError as e:
            raise OCRProcessingError(
                f"Tesseract OCR is not installed or not found in PATH: {str(e)}"
            )
        except Exception as e:
            raise OCRProcessingError(
                f"OCR processing failed: {str(e)}"
            )
    
    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Preprocess an image to improve OCR accuracy.
        
        Applies image enhancement techniques such as grayscale conversion,
        contrast adjustment, and noise reduction to improve text recognition
        quality, especially for low-quality scans.
        
        Args:
            image: PIL Image object to preprocess
            
        Returns:
            Preprocessed PIL Image object
            
        Requirements:
            - 7.2: Attempt preprocessing to improve recognition for poor quality images
        """
        from PIL import ImageEnhance, ImageFilter, ImageOps
        import numpy as np
        
        # Step 1: Convert to grayscale if not already
        if image.mode != 'L':
            image = image.convert('L')
        
        # Step 2: Increase image size for better OCR (if too small)
        # OCR works better with larger text
        width, height = image.size
        if width < 1800 or height < 1800:
            scale_factor = max(1800 / width, 1800 / height)
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Step 3: Apply adaptive thresholding for better text/background separation
        # Convert to numpy array for processing
        img_array = np.array(image)
        
        # Calculate adaptive threshold
        from scipy import ndimage
        # Apply Gaussian blur for local threshold calculation
        blurred = ndimage.gaussian_filter(img_array, sigma=5)
        
        # Threshold: pixels darker than local average become black, others white
        threshold = img_array > (blurred - 10)
        img_array = np.where(threshold, 255, 0).astype(np.uint8)
        
        image = Image.fromarray(img_array)
        
        # Step 4: Apply contrast adjustment to enhance text visibility
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)
        
        # Step 5: Apply sharpening to enhance text edges
        image = image.filter(ImageFilter.SHARPEN)
        
        return image
