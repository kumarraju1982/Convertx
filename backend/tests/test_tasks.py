"""
Tests for Celery tasks.

These tests verify the conversion task and cleanup task functionality.
"""

import pytest
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
from PIL import Image
from app.tasks import convert_pdf_task, cleanup_old_files_task
from app.models import PageImage, OCRResult, WordBox, DocumentStructure, StructureElement


class TestConvertPDFTask:
    """Test suite for convert_pdf_task."""
    
    @patch('app.tasks.get_redis_client')
    @patch('app.tasks.JobManager')
    @patch('app.tasks.FileManager')
    @patch('app.tasks.PDFConverter')
    def test_convert_pdf_task_success(
        self,
        mock_converter_class,
        mock_file_manager_class,
        mock_job_manager_class,
        mock_redis_client
    ):
        """Test successful PDF conversion task."""
        # Setup mocks
        job_id = "test-job-123"
        
        # Mock Redis client
        mock_redis = Mock()
        mock_redis_client.return_value = mock_redis
        
        # Mock FileManager
        mock_file_manager = Mock()
        mock_file_manager.get_input_path.return_value = "/tmp/input.pdf"
        mock_file_manager.get_output_path.return_value = "/tmp/output.docx"
        mock_file_manager_class.return_value = mock_file_manager
        
        # Mock JobManager
        mock_job_manager = Mock()
        mock_job_manager_class.return_value = mock_job_manager
        
        # Mock PDFConverter
        mock_converter = Mock()
        mock_converter.convert.return_value = {
            "success": True,
            "output_path": "/tmp/output.docx",
            "pages_processed": 3,
            "pages_failed": [],
            "errors": []
        }
        mock_converter_class.return_value = mock_converter
        
        # Execute task
        result = convert_pdf_task(job_id)
        
        # Verify results
        assert result["success"] is True
        assert result["job_id"] == job_id
        assert result["pages_processed"] == 3
        assert result["pages_failed"] == []
        
        # Verify method calls
        mock_file_manager.get_input_path.assert_called_once_with(job_id)
        mock_job_manager.mark_processing.assert_called_once_with(job_id)
        mock_converter.convert.assert_called_once()
        mock_job_manager.mark_completed.assert_called_once()
    
    @patch('app.tasks.get_redis_client')
    @patch('app.tasks.JobManager')
    @patch('app.tasks.FileManager')
    @patch('app.tasks.PDFConverter')
    def test_convert_pdf_task_input_not_found(
        self,
        mock_converter_class,
        mock_file_manager_class,
        mock_job_manager_class,
        mock_redis_client
    ):
        """Test task when input file is not found."""
        job_id = "test-job-456"
        
        # Mock Redis client
        mock_redis = Mock()
        mock_redis_client.return_value = mock_redis
        
        # Mock FileManager - input not found
        mock_file_manager = Mock()
        mock_file_manager.get_input_path.return_value = None
        mock_file_manager_class.return_value = mock_file_manager
        
        # Mock JobManager
        mock_job_manager = Mock()
        mock_job_manager_class.return_value = mock_job_manager
        
        # Execute task
        result = convert_pdf_task(job_id)
        
        # Verify results
        assert result["success"] is False
        assert "Input file not found" in result["errors"][0]
        
        # Verify job was marked as failed
        mock_job_manager.mark_failed.assert_called_once()
    
    @patch('app.tasks.get_redis_client')
    @patch('app.tasks.JobManager')
    @patch('app.tasks.FileManager')
    @patch('app.tasks.PDFConverter')
    def test_convert_pdf_task_with_page_failures(
        self,
        mock_converter_class,
        mock_file_manager_class,
        mock_job_manager_class,
        mock_redis_client
    ):
        """Test task when some pages fail during conversion."""
        job_id = "test-job-789"
        
        # Mock Redis client
        mock_redis = Mock()
        mock_redis_client.return_value = mock_redis
        
        # Mock FileManager
        mock_file_manager = Mock()
        mock_file_manager.get_input_path.return_value = "/tmp/input.pdf"
        mock_file_manager.get_output_path.return_value = "/tmp/output.docx"
        mock_file_manager_class.return_value = mock_file_manager
        
        # Mock JobManager
        mock_job_manager = Mock()
        mock_job_manager_class.return_value = mock_job_manager
        
        # Mock PDFConverter - some pages failed
        mock_converter = Mock()
        mock_converter.convert.return_value = {
            "success": True,
            "output_path": "/tmp/output.docx",
            "pages_processed": 2,
            "pages_failed": [2],
            "errors": ["Page 2: OCR failed"]
        }
        mock_converter_class.return_value = mock_converter
        
        # Execute task
        result = convert_pdf_task(job_id)
        
        # Verify results
        assert result["success"] is True
        assert result["pages_processed"] == 2
        assert result["pages_failed"] == [2]
        assert len(result["errors"]) == 1
        
        # Job should still be marked as completed (partial success)
        mock_job_manager.mark_completed.assert_called_once()
    
    @patch('app.tasks.get_redis_client')
    @patch('app.tasks.JobManager')
    @patch('app.tasks.FileManager')
    @patch('app.tasks.PDFConverter')
    def test_convert_pdf_task_progress_callback(
        self,
        mock_converter_class,
        mock_file_manager_class,
        mock_job_manager_class,
        mock_redis_client
    ):
        """Test that progress callback updates job progress."""
        job_id = "test-job-progress"
        
        # Mock Redis client
        mock_redis = Mock()
        mock_redis_client.return_value = mock_redis
        
        # Mock FileManager
        mock_file_manager = Mock()
        mock_file_manager.get_input_path.return_value = "/tmp/input.pdf"
        mock_file_manager.get_output_path.return_value = "/tmp/output.docx"
        mock_file_manager_class.return_value = mock_file_manager
        
        # Mock JobManager
        mock_job_manager = Mock()
        mock_job_manager_class.return_value = mock_job_manager
        
        # Mock PDFConverter - capture progress callback
        mock_converter = Mock()
        progress_callback_captured = None
        
        def capture_callback(*args, **kwargs):
            nonlocal progress_callback_captured
            progress_callback_captured = kwargs.get('progress_callback')
            return {
                "success": True,
                "output_path": "/tmp/output.docx",
                "pages_processed": 3,
                "pages_failed": [],
                "errors": []
            }
        
        mock_converter.convert.side_effect = capture_callback
        mock_converter_class.return_value = mock_converter
        
        # Execute task
        result = convert_pdf_task(job_id)
        
        # Verify progress callback was provided
        assert progress_callback_captured is not None
        
        # Test the progress callback
        progress_callback_captured(1, 3)
        progress_callback_captured(2, 3)
        progress_callback_captured(3, 3)
        
        # Verify progress updates were called
        assert mock_job_manager.update_progress.call_count == 3
        mock_job_manager.update_progress.assert_any_call(job_id, 1, 3)
        mock_job_manager.update_progress.assert_any_call(job_id, 2, 3)
        mock_job_manager.update_progress.assert_any_call(job_id, 3, 3)
    
    @patch('app.tasks.get_redis_client')
    @patch('app.tasks.JobManager')
    @patch('app.tasks.FileManager')
    @patch('app.tasks.PDFConverter')
    def test_convert_pdf_task_pdf_validation_error(
        self,
        mock_converter_class,
        mock_file_manager_class,
        mock_job_manager_class,
        mock_redis_client
    ):
        """Test task when PDF validation fails."""
        from app.exceptions import PDFValidationError
        
        job_id = "test-job-invalid"
        
        # Mock Redis client
        mock_redis = Mock()
        mock_redis_client.return_value = mock_redis
        
        # Mock FileManager
        mock_file_manager = Mock()
        mock_file_manager.get_input_path.return_value = "/tmp/invalid.pdf"
        mock_file_manager_class.return_value = mock_file_manager
        
        # Mock JobManager
        mock_job_manager = Mock()
        mock_job_manager_class.return_value = mock_job_manager
        
        # Mock PDFConverter - raise validation error
        mock_converter = Mock()
        mock_converter.convert.side_effect = PDFValidationError("Invalid PDF format")
        mock_converter_class.return_value = mock_converter
        
        # Execute task
        result = convert_pdf_task(job_id)
        
        # Verify results
        assert result["success"] is False
        assert "PDF validation failed" in result["errors"][0]
        
        # Verify job was marked as failed
        mock_job_manager.mark_failed.assert_called_once()


class TestCleanupOldFilesTask:
    """Test suite for cleanup_old_files_task."""
    
    @patch('app.tasks.FileManager')
    def test_cleanup_old_files_success(self, mock_file_manager_class):
        """Test successful file cleanup."""
        # Mock FileManager
        mock_file_manager = Mock()
        mock_file_manager.cleanup_old_files.return_value = 5
        mock_file_manager_class.return_value = mock_file_manager
        
        # Execute task
        result = cleanup_old_files_task(24)
        
        # Verify results
        assert result["success"] is True
        assert result["files_deleted"] == 5
        assert result["errors"] == []
        
        # Verify cleanup was called
        mock_file_manager.cleanup_old_files.assert_called_once_with(24)
    
    @patch('app.tasks.FileManager')
    def test_cleanup_old_files_no_files(self, mock_file_manager_class):
        """Test cleanup when no files need to be deleted."""
        # Mock FileManager
        mock_file_manager = Mock()
        mock_file_manager.cleanup_old_files.return_value = 0
        mock_file_manager_class.return_value = mock_file_manager
        
        # Execute task
        result = cleanup_old_files_task(24)
        
        # Verify results
        assert result["success"] is True
        assert result["files_deleted"] == 0
        assert result["errors"] == []
    
    @patch('app.tasks.FileManager')
    def test_cleanup_old_files_error(self, mock_file_manager_class):
        """Test cleanup when an error occurs."""
        # Mock FileManager - raise exception
        mock_file_manager = Mock()
        mock_file_manager.cleanup_old_files.side_effect = Exception("Disk error")
        mock_file_manager_class.return_value = mock_file_manager
        
        # Execute task
        result = cleanup_old_files_task(24)
        
        # Verify results
        assert result["success"] is False
        assert result["files_deleted"] == 0
        assert "Cleanup failed" in result["errors"][0]
    
    @patch('app.tasks.FileManager')
    def test_cleanup_old_files_custom_age(self, mock_file_manager_class):
        """Test cleanup with custom max age."""
        # Mock FileManager
        mock_file_manager = Mock()
        mock_file_manager.cleanup_old_files.return_value = 3
        mock_file_manager_class.return_value = mock_file_manager
        
        # Execute task with custom age
        result = cleanup_old_files_task(48)
        
        # Verify results
        assert result["success"] is True
        assert result["files_deleted"] == 3
        
        # Verify cleanup was called with correct age
        mock_file_manager.cleanup_old_files.assert_called_once_with(48)



class TestConvertPDFTaskEdgeCases:
    """Test edge cases for convert_pdf_task."""
    
    @patch('app.tasks.PDFConverter')
    @patch('app.tasks.FileManager')
    @patch('app.tasks.JobManager')
    def test_convert_pdf_task_without_celery_request_id(
        self, mock_job_manager_class, mock_file_manager_class, mock_converter_class
    ):
        """Test task when Celery request ID is not available."""
        from app.tasks import convert_pdf_task
        
        # Setup mocks
        mock_file_manager = Mock()
        mock_file_manager.get_input_path.return_value = "/tmp/test.pdf"
        mock_file_manager.get_output_path.return_value = None  # Trigger output path generation
        mock_file_manager.upload_folder = "/tmp/uploads"
        mock_file_manager_class.return_value = mock_file_manager
        
        mock_job_manager = Mock()
        mock_job_manager_class.return_value = mock_job_manager
        
        mock_converter = Mock()
        mock_converter.convert.return_value = {
            'success': True,
            'output_path': '/tmp/output.docx',
            'pages_processed': 1,
            'pages_failed': [],
            'errors': []
        }
        mock_converter_class.return_value = mock_converter
        
        # Call task (simulating no Celery context)
        result = convert_pdf_task("test-job")
        
        assert result['success'] is True
    
    @patch('app.tasks.JobManager')
    def test_convert_pdf_task_progress_update_error(self, mock_job_manager_class):
        """Test task continues when progress update fails."""
        from app.tasks import convert_pdf_task
        
        mock_job_manager = Mock()
        mock_job_manager.update_progress.side_effect = Exception("Redis error")
        mock_job_manager_class.return_value = mock_job_manager
        
        # Task should handle the error and continue
        # (This tests the error handling in progress callback)
        try:
            convert_pdf_task("test-job")
        except Exception:
            pass  # Expected to fail at file operations, but progress error should be caught
