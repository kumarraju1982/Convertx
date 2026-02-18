"""
Unit tests for Surya OCR Engine component.

Tests the SuryaOCREngine class functionality including text extraction,
layout analysis, and error handling.

Requirements:
- 2.1: Extract all visible text content
- 3.1: Layout structure detection
"""

import pytest
from PIL import Image, ImageDraw
from unittest.mock import Mock, patch, MagicMock
from app.surya_ocr_engine import SuryaOCREngine
from app.models import OCRResult, WordBox
from app.exceptions import OCRProcessingError


@pytest.fixture
def surya_engine():
    """Create a SuryaOCREngine instance for testing."""
    return SuryaOCREngine()


@pytest.fixture
def simple_text_image():
    """Create a simple image with text for testing."""
    img = Image.new('RGB', (400, 100), color='white')
    draw = ImageDraw.Draw(img)
    draw.text((10, 30), "Hello World", fill='black')
    return img


@pytest.fixture
def blank_image():
    """Create a blank white image with no text."""
    return Image.new('RGB', (400, 100), color='white')


@pytest.fixture
def large_image():
    """Create a large image that needs resizing."""
    return Image.new('RGB', (4000, 3000), color='white')


class TestSuryaOCREngineInitialization:
    """Test SuryaOCREngine initialization."""
    
    def test_initialization(self):
        """Test that SuryaOCREngine can be instantiated."""
        engine = SuryaOCREngine()
        assert engine is not None
        assert engine._initialized is False
    
    def test_lazy_initialization(self, surya_engine):
        """Test that models are not loaded until first use."""
        # After creation, should not be initialized
        assert surya_engine._initialized is False
        assert surya_engine._model is None


class TestPreprocessImage:
    """Test image preprocessing functionality."""
    
    def test_preprocess_converts_to_rgb(self, surya_engine):
        """Test that preprocessing converts images to RGB."""
        # Create a grayscale image
        gray_img = Image.new('L', (100, 100), color=128)
        
        result = surya_engine.preprocess_image(gray_img)
        
        # Should be converted to RGB
        assert result.mode == 'RGB'
    
    def test_preprocess_preserves_rgb(self, surya_engine):
        """Test that RGB images are preserved."""
        rgb_img = Image.new('RGB', (100, 100), color=(255, 0, 0))
        
        result = surya_engine.preprocess_image(rgb_img)
        
        # Should remain RGB
        assert result.mode == 'RGB'
    
    def test_preprocess_returns_image(self, surya_engine):
        """Test that preprocessing returns a PIL Image."""
        img = Image.new('RGB', (100, 100), color='white')
        
        result = surya_engine.preprocess_image(img)
        
        assert isinstance(result, Image.Image)
    
    def test_preprocess_resizes_large_images(self, surya_engine, large_image):
        """Test that very large images are resized (Requirement 7.2)."""
        result = surya_engine.preprocess_image(large_image)
        
        # Should be resized to max dimension of 3000
        assert max(result.size) <= 3000
        assert result.mode == 'RGB'
    
    def test_preprocess_maintains_aspect_ratio(self, surya_engine):
        """Test that preprocessing maintains aspect ratio when resizing."""
        # Create a 4000x2000 image (2:1 aspect ratio)
        img = Image.new('RGB', (4000, 2000), color='white')
        
        result = surya_engine.preprocess_image(img)
        
        # Should maintain 2:1 aspect ratio
        width, height = result.size
        aspect_ratio = width / height
        assert abs(aspect_ratio - 2.0) < 0.1  # Allow small tolerance
    
    def test_preprocess_does_not_resize_small_images(self, surya_engine, simple_text_image):
        """Test that small images are not resized."""
        original_size = simple_text_image.size
        
        result = surya_engine.preprocess_image(simple_text_image)
        
        # Size should be preserved
        assert result.size == original_size
    
    def test_preprocess_with_rgba_image(self, surya_engine):
        """Test that RGBA images are converted to RGB."""
        rgba_img = Image.new('RGBA', (100, 100), color=(255, 0, 0, 128))
        
        result = surya_engine.preprocess_image(rgba_img)
        
        # Should be converted to RGB
        assert result.mode == 'RGB'


class TestExtractTextMocked:
    """Test text extraction with mocked Surya OCR."""
    
    def test_extract_text_calls_preprocess(self, surya_engine, simple_text_image):
        """Test that extract_text calls preprocess_image."""
        with patch.object(surya_engine, 'preprocess_image', wraps=surya_engine.preprocess_image) as mock_preprocess:
            with patch.object(surya_engine, '_ensure_initialized'):
                with patch('surya.ocr.run_ocr', return_value=[]):
                    try:
                        surya_engine.extract_text(simple_text_image)
                    except:
                        pass  # We're just testing that preprocess was called
                    
                    mock_preprocess.assert_called_once()
    
    def test_extract_text_handles_empty_results(self, surya_engine, simple_text_image):
        """Test handling when Surya returns no results."""
        # Mock the models to be initialized
        surya_engine._initialized = True
        surya_engine._det_model = Mock()
        surya_engine._det_processor = Mock()
        surya_engine._rec_model = Mock()
        surya_engine._rec_processor = Mock()
        
        with patch('surya.ocr.run_ocr', return_value=[]):
            result = surya_engine.extract_text(simple_text_image)
            
            assert isinstance(result, OCRResult)
            assert result.text == ""
            assert len(result.words) == 0
            assert result.confidence == 0.0


class TestErrorHandling:
    """Test error handling in Surya OCR processing."""
    
    def test_extract_text_handles_ocr_failure(self, surya_engine, simple_text_image):
        """Test that OCR failures raise OCRProcessingError."""
        with patch.object(surya_engine, '_ensure_initialized'):
            with patch('surya.ocr.run_ocr', side_effect=Exception("OCR failed")):
                with pytest.raises(OCRProcessingError) as exc_info:
                    surya_engine.extract_text(simple_text_image)
                
                assert "Surya OCR processing failed" in str(exc_info.value)
    
    def test_ensure_initialized_handles_import_error(self, surya_engine):
        """Test that missing Surya installation raises appropriate error."""
        with patch('builtins.__import__', side_effect=ImportError("No module named 'surya'")):
            with pytest.raises(OCRProcessingError) as exc_info:
                surya_engine._ensure_initialized()
            
            assert "Surya OCR is not installed" in str(exc_info.value)


class TestLayoutAnalysis:
    """Test layout analysis functionality."""
    
    def test_get_layout_analysis_returns_dict(self, surya_engine, simple_text_image):
        """Test that layout analysis returns a dictionary (Requirement 3.1)."""
        with patch.object(surya_engine, '_ensure_initialized'):
            with patch('surya.layout.batch_layout_detection', return_value=[{'tables': []}]):
                result = surya_engine.get_layout_analysis(simple_text_image)
                
                assert isinstance(result, dict)
    
    def test_get_layout_analysis_handles_failure(self, surya_engine, simple_text_image):
        """Test that layout analysis failures are handled gracefully."""
        with patch.object(surya_engine, '_ensure_initialized'):
            with patch('surya.layout.batch_layout_detection', side_effect=Exception("Layout failed")):
                result = surya_engine.get_layout_analysis(simple_text_image)
                
                # Should return empty dict on failure
                assert isinstance(result, dict)
                assert len(result) == 0
    
    def test_get_layout_analysis_no_results(self, surya_engine, simple_text_image):
        """Test handling when layout detection returns no results."""
        with patch.object(surya_engine, '_ensure_initialized'):
            with patch('surya.layout.batch_layout_detection', return_value=[]):
                result = surya_engine.get_layout_analysis(simple_text_image)
                
                # Should return empty dict
                assert isinstance(result, dict)
                assert len(result) == 0


class TestModelCaching:
    """Test that models are loaded once and cached."""
    
    def test_initialization_flag_prevents_reload(self, surya_engine):
        """Test that _initialized flag prevents reloading models."""
        # Manually set the engine as initialized
        surya_engine._initialized = True
        surya_engine._det_model = Mock()
        surya_engine._det_processor = Mock()
        surya_engine._rec_model = Mock()
        surya_engine._rec_processor = Mock()
        
        # Store references
        det_model_ref = surya_engine._det_model
        det_proc_ref = surya_engine._det_processor
        rec_model_ref = surya_engine._rec_model
        rec_proc_ref = surya_engine._rec_processor
        
        # Call ensure_initialized multiple times
        surya_engine._ensure_initialized()
        surya_engine._ensure_initialized()
        surya_engine._ensure_initialized()
        
        # Models should still be the same objects (not reloaded)
        assert surya_engine._det_model is det_model_ref
        assert surya_engine._det_processor is det_proc_ref
        assert surya_engine._rec_model is rec_model_ref
        assert surya_engine._rec_processor is rec_proc_ref
        assert surya_engine._initialized is True
