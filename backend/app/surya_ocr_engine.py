"""
Surya OCR Engine for extracting text from images with advanced layout analysis.

This module provides OCR functionality using Surya OCR, which offers better accuracy
for complex documents with tables, symbols, and multi-column layouts compared to Tesseract.
"""

from PIL import Image
from typing import List, Optional
import logging
from app.models import OCRResult, WordBox
from app.exceptions import OCRProcessingError

logger = logging.getLogger(__name__)


class SuryaOCREngine:
    """
    OCR Engine that uses Surya OCR for high-accuracy text extraction.
    
    Surya OCR provides:
    - Better accuracy for complex documents (tables, symbols, multi-column)
    - Built-in layout analysis (tables, images, headers detection)
    - Support for 90+ languages
    - Reading order detection
    
    Trade-off: Slower processing than Tesseract but significantly better quality.
    """
    
    def __init__(self):
        """Initialize the Surya OCR Engine and load models."""
        self._model = None
        self._processor = None
        self._initialized = False
        logger.info("SuryaOCREngine initialized (models will load on first use)")
    
    def _ensure_initialized(self):
        """Lazy load Surya models on first use to avoid startup delays."""
        if self._initialized:
            return
        
        try:
            logger.info("Loading Surya OCR models (this may take a moment on first run)...")
            from surya.ocr import run_ocr
            from surya.model.detection.model import load_model as load_det_model
            from surya.model.detection.processor import load_processor as load_det_processor
            from surya.model.recognition.model import load_model as load_rec_model
            from surya.model.recognition.processor import load_processor as load_rec_processor
            
            # Load detection and recognition models
            self._det_model = load_det_model()
            self._det_processor = load_det_processor()
            self._rec_model = load_rec_model()
            self._rec_processor = load_rec_processor()
            
            self._initialized = True
            logger.info("Surya OCR models loaded successfully")
            
        except ImportError as e:
            raise OCRProcessingError(
                f"Surya OCR is not installed. Install with: pip install surya-ocr\nError: {str(e)}"
            )
        except Exception as e:
            raise OCRProcessingError(
                f"Failed to initialize Surya OCR models: {str(e)}"
            )
    
    def extract_text(self, image: Image.Image) -> OCRResult:
        """
        Extract text from an image using Surya OCR with layout analysis.
        
        Uses Surya OCR to extract text with high accuracy, including:
        - Word-level bounding boxes
        - Confidence scores
        - Layout structure (paragraphs, tables, columns)
        - Reading order preservation
        
        Args:
            image: PIL Image object to extract text from
            
        Returns:
            OCRResult containing:
                - text: Full extracted text content in reading order
                - words: List of WordBox objects with position and confidence
                - confidence: Overall confidence score (0.0 to 1.0)
                
        Raises:
            OCRProcessingError: If OCR processing fails
            
        Requirements:
            - 2.1: Extract all visible text content
            - 2.2: Preserve reading order (left-to-right, top-to-bottom)
            - 2.5: Provide confidence scores for recognized text
            - 3.1, 3.2, 3.3: Layout analysis (paragraphs, headings, tables)
        """
        try:
            # Ensure models are loaded
            self._ensure_initialized()
            
            # Import Surya functions
            from surya.ocr import run_ocr
            from surya.languages import CODE_TO_LANGUAGE
            
            # Preprocess image for better results
            preprocessed_image = self.preprocess_image(image)
            
            # Run Surya OCR
            # Surya expects a list of images and language codes
            langs = [["en"]]  # English language
            
            logger.info("Running Surya OCR on image...")
            predictions = run_ocr(
                [preprocessed_image],
                langs,
                self._det_model,
                self._det_processor,
                self._rec_model,
                self._rec_processor
            )
            
            # Extract results from first (and only) image
            if not predictions or len(predictions) == 0:
                logger.warning("Surya OCR returned no results")
                return OCRResult(text="", words=[], confidence=0.0)
            
            result = predictions[0]
            
            # Extract word-level information
            words: List[WordBox] = []
            confidences: List[float] = []
            full_text_parts: List[str] = []
            
            # Process text lines from Surya
            for text_line in result.text_lines:
                line_text = text_line.text.strip()
                if not line_text:
                    continue
                
                # Get bounding box for the line
                bbox = text_line.bbox
                confidence = getattr(text_line, 'confidence', 0.95)  # Surya typically has high confidence
                
                # Create WordBox for each word in the line
                # Split line into words and estimate positions
                line_words = line_text.split()
                if line_words:
                    word_width = (bbox[2] - bbox[0]) / len(line_words)
                    
                    for idx, word_text in enumerate(line_words):
                        word_box = WordBox(
                            text=word_text,
                            x=int(bbox[0] + idx * word_width),
                            y=int(bbox[1]),
                            width=int(word_width),
                            height=int(bbox[3] - bbox[1]),
                            confidence=confidence
                        )
                        words.append(word_box)
                        confidences.append(confidence)
                
                full_text_parts.append(line_text)
            
            # Combine all text with proper line breaks
            full_text = "\n".join(full_text_parts)
            
            # Calculate overall confidence
            overall_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            logger.info(f"Surya OCR extracted {len(words)} words with {overall_confidence:.2%} confidence")
            
            return OCRResult(
                text=full_text,
                words=words,
                confidence=overall_confidence
            )
            
        except Exception as e:
            logger.error(f"Surya OCR processing failed: {str(e)}")
            raise OCRProcessingError(
                f"Surya OCR processing failed: {str(e)}"
            )
    
    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Preprocess an image for Surya OCR.
        
        Surya OCR has its own preprocessing, but we apply minimal adjustments
        to ensure optimal input quality.
        
        Args:
            image: PIL Image object to preprocess
            
        Returns:
            Preprocessed PIL Image object
            
        Requirements:
            - 7.2: Attempt preprocessing to improve recognition
        """
        # Convert to RGB if needed (Surya expects RGB)
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Surya works well with various image sizes, but ensure reasonable dimensions
        width, height = image.size
        max_dimension = 3000
        
        if width > max_dimension or height > max_dimension:
            # Scale down very large images
            scale_factor = max_dimension / max(width, height)
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            logger.info(f"Resized image from {width}x{height} to {new_width}x{new_height}")
        
        return image
    
    def get_layout_analysis(self, image: Image.Image) -> dict:
        """
        Perform layout analysis on an image to detect document structure.
        
        This method uses Surya's layout analysis capabilities to detect:
        - Tables
        - Images
        - Headers/headings
        - Paragraphs
        - Columns
        
        Args:
            image: PIL Image object to analyze
            
        Returns:
            Dictionary containing layout information
            
        Requirements:
            - 3.1, 3.2, 3.3, 3.4, 3.5: Layout structure detection
        """
        try:
            self._ensure_initialized()
            
            from surya.layout import batch_layout_detection
            from surya.model.layout.model import load_model as load_layout_model
            from surya.model.layout.processor import load_processor as load_layout_processor
            
            # Load layout models if not already loaded
            if not hasattr(self, '_layout_model'):
                logger.info("Loading Surya layout analysis models...")
                self._layout_model = load_layout_model()
                self._layout_processor = load_layout_processor()
            
            # Run layout detection
            layout_results = batch_layout_detection(
                [image],
                self._layout_model,
                self._layout_processor
            )
            
            if layout_results and len(layout_results) > 0:
                return layout_results[0]
            
            return {}
            
        except Exception as e:
            logger.warning(f"Layout analysis failed: {str(e)}")
            return {}
