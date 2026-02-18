"""
Unit tests for JobManager class.

Tests job creation, state transitions, progress tracking, and error handling.
"""

import pytest
import json
from datetime import datetime
from unittest.mock import Mock, patch
from app.job_manager import JobManager
from app.exceptions import JobNotFoundError


@pytest.fixture
def mock_redis():
    """Create a mock Redis client."""
    return Mock()


@pytest.fixture
def job_manager(mock_redis):
    """Create a JobManager instance with mock Redis."""
    return JobManager(redis_client=mock_redis)


class TestJobCreation:
    """Tests for job creation functionality."""
    
    def test_create_job_generates_unique_id(self, job_manager, mock_redis):
        """Test that create_job generates a unique job ID."""
        file_path = "/uploads/test.pdf"
        
        job_id = job_manager.create_job(file_path)
        
        # Verify job_id is a valid UUID string
        assert isinstance(job_id, str)
        assert len(job_id) == 36  # UUID format: 8-4-4-4-12
        assert job_id.count('-') == 4
        
        # Verify Redis setex was called
        assert mock_redis.setex.called
    
    def test_create_job_initializes_pending_status(self, job_manager, mock_redis):
        """Test that new jobs start with 'pending' status."""
        file_path = "/uploads/test.pdf"
        
        job_id = job_manager.create_job(file_path)
        
        # Get the data that was stored in Redis
        call_args = mock_redis.setex.call_args
        stored_data = json.loads(call_args[0][2])
        
        assert stored_data["status"] == "pending"
        assert stored_data["job_id"] == job_id
        assert stored_data["file_path"] == file_path
    
    def test_create_job_initializes_progress_to_zero(self, job_manager, mock_redis):
        """Test that new jobs have progress initialized to zero."""
        file_path = "/uploads/test.pdf"
        
        job_manager.create_job(file_path)
        
        # Get the data that was stored in Redis
        call_args = mock_redis.setex.call_args
        stored_data = json.loads(call_args[0][2])
        
        assert stored_data["progress"]["current_page"] == 0
        assert stored_data["progress"]["total_pages"] == 0
        assert stored_data["progress"]["percentage"] == 0
    
    def test_create_job_sets_timestamps(self, job_manager, mock_redis):
        """Test that new jobs have created_at and updated_at timestamps."""
        file_path = "/uploads/test.pdf"
        
        job_manager.create_job(file_path)
        
        # Get the data that was stored in Redis
        call_args = mock_redis.setex.call_args
        stored_data = json.loads(call_args[0][2])
        
        assert "created_at" in stored_data
        assert "updated_at" in stored_data
        
        # Verify timestamps are valid ISO format
        datetime.fromisoformat(stored_data["created_at"])
        datetime.fromisoformat(stored_data["updated_at"])
    
    def test_create_job_sets_expiration(self, job_manager, mock_redis):
        """Test that jobs are stored with expiration time."""
        file_path = "/uploads/test.pdf"
        
        job_manager.create_job(file_path)
        
        # Verify setex was called with correct expiration
        call_args = mock_redis.setex.call_args
        expiration = call_args[0][1]
        
        assert expiration == JobManager.JOB_EXPIRATION_SECONDS


class TestProgressUpdates:
    """Tests for progress update functionality."""
    
    def test_update_progress_stores_page_counts(self, job_manager, mock_redis):
        """Test that update_progress stores current and total page counts."""
        job_id = "test-job-123"
        
        # Mock existing job data
        existing_data = {
            "job_id": job_id,
            "status": "processing",
            "progress": {"current_page": 0, "total_pages": 0, "percentage": 0}
        }
        mock_redis.get.return_value = json.dumps(existing_data)
        
        job_manager.update_progress(job_id, current_page=3, total_pages=10)
        
        # Get the updated data
        call_args = mock_redis.setex.call_args
        updated_data = json.loads(call_args[0][2])
        
        assert updated_data["progress"]["current_page"] == 3
        assert updated_data["progress"]["total_pages"] == 10
    
    def test_update_progress_calculates_percentage(self, job_manager, mock_redis):
        """Test that update_progress calculates percentage correctly."""
        job_id = "test-job-123"
        
        # Mock existing job data
        existing_data = {
            "job_id": job_id,
            "status": "processing",
            "progress": {"current_page": 0, "total_pages": 0, "percentage": 0}
        }
        mock_redis.get.return_value = json.dumps(existing_data)
        
        job_manager.update_progress(job_id, current_page=5, total_pages=10)
        
        # Get the updated data
        call_args = mock_redis.setex.call_args
        updated_data = json.loads(call_args[0][2])
        
        assert updated_data["progress"]["percentage"] == 50
    
    def test_update_progress_handles_zero_total_pages(self, job_manager, mock_redis):
        """Test that update_progress handles zero total pages without error."""
        job_id = "test-job-123"
        
        # Mock existing job data
        existing_data = {
            "job_id": job_id,
            "status": "processing",
            "progress": {"current_page": 0, "total_pages": 0, "percentage": 0}
        }
        mock_redis.get.return_value = json.dumps(existing_data)
        
        job_manager.update_progress(job_id, current_page=0, total_pages=0)
        
        # Get the updated data
        call_args = mock_redis.setex.call_args
        updated_data = json.loads(call_args[0][2])
        
        assert updated_data["progress"]["percentage"] == 0
    
    def test_update_progress_updates_timestamp(self, job_manager, mock_redis):
        """Test that update_progress updates the updated_at timestamp."""
        job_id = "test-job-123"
        
        # Mock existing job data
        existing_data = {
            "job_id": job_id,
            "status": "processing",
            "progress": {"current_page": 0, "total_pages": 0, "percentage": 0},
            "updated_at": "2024-01-01T00:00:00"
        }
        mock_redis.get.return_value = json.dumps(existing_data)
        
        job_manager.update_progress(job_id, current_page=1, total_pages=10)
        
        # Get the updated data
        call_args = mock_redis.setex.call_args
        updated_data = json.loads(call_args[0][2])
        
        assert updated_data["updated_at"] != "2024-01-01T00:00:00"
    
    def test_update_progress_raises_on_nonexistent_job(self, job_manager, mock_redis):
        """Test that update_progress raises JobNotFoundError for nonexistent job."""
        job_id = "nonexistent-job"
        mock_redis.get.return_value = None
        
        with pytest.raises(JobNotFoundError) as exc_info:
            job_manager.update_progress(job_id, current_page=1, total_pages=10)
        
        assert job_id in str(exc_info.value)


class TestStateTransitions:
    """Tests for job state transition methods."""
    
    def test_mark_processing_changes_status(self, job_manager, mock_redis):
        """Test that mark_processing changes status to 'processing'."""
        job_id = "test-job-123"
        
        # Mock existing job data
        existing_data = {
            "job_id": job_id,
            "status": "pending"
        }
        mock_redis.get.return_value = json.dumps(existing_data)
        
        job_manager.mark_processing(job_id)
        
        # Get the updated data
        call_args = mock_redis.setex.call_args
        updated_data = json.loads(call_args[0][2])
        
        assert updated_data["status"] == "processing"
    
    def test_mark_completed_changes_status(self, job_manager, mock_redis):
        """Test that mark_completed changes status to 'completed'."""
        job_id = "test-job-123"
        output_path = "/uploads/test-job-123/output.docx"
        
        # Mock existing job data
        existing_data = {
            "job_id": job_id,
            "status": "processing",
            "progress": {"current_page": 5, "total_pages": 10, "percentage": 50}
        }
        mock_redis.get.return_value = json.dumps(existing_data)
        
        job_manager.mark_completed(job_id, output_path)
        
        # Get the updated data
        call_args = mock_redis.setex.call_args
        updated_data = json.loads(call_args[0][2])
        
        assert updated_data["status"] == "completed"
        assert updated_data["output_path"] == output_path
    
    def test_mark_completed_sets_progress_to_100(self, job_manager, mock_redis):
        """Test that mark_completed sets progress to 100%."""
        job_id = "test-job-123"
        output_path = "/uploads/test-job-123/output.docx"
        
        # Mock existing job data
        existing_data = {
            "job_id": job_id,
            "status": "processing",
            "progress": {"current_page": 5, "total_pages": 10, "percentage": 50}
        }
        mock_redis.get.return_value = json.dumps(existing_data)
        
        job_manager.mark_completed(job_id, output_path)
        
        # Get the updated data
        call_args = mock_redis.setex.call_args
        updated_data = json.loads(call_args[0][2])
        
        assert updated_data["progress"]["percentage"] == 100
        assert updated_data["progress"]["current_page"] == 10
    
    def test_mark_completed_sets_timestamp(self, job_manager, mock_redis):
        """Test that mark_completed sets completed_at timestamp."""
        job_id = "test-job-123"
        output_path = "/uploads/test-job-123/output.docx"
        
        # Mock existing job data
        existing_data = {
            "job_id": job_id,
            "status": "processing",
            "progress": {"current_page": 5, "total_pages": 10, "percentage": 50}
        }
        mock_redis.get.return_value = json.dumps(existing_data)
        
        job_manager.mark_completed(job_id, output_path)
        
        # Get the updated data
        call_args = mock_redis.setex.call_args
        updated_data = json.loads(call_args[0][2])
        
        assert "completed_at" in updated_data
        datetime.fromisoformat(updated_data["completed_at"])
    
    def test_mark_failed_changes_status(self, job_manager, mock_redis):
        """Test that mark_failed changes status to 'failed'."""
        job_id = "test-job-123"
        error_message = "OCR processing failed on page 3"
        
        # Mock existing job data
        existing_data = {
            "job_id": job_id,
            "status": "processing"
        }
        mock_redis.get.return_value = json.dumps(existing_data)
        
        job_manager.mark_failed(job_id, error_message)
        
        # Get the updated data
        call_args = mock_redis.setex.call_args
        updated_data = json.loads(call_args[0][2])
        
        assert updated_data["status"] == "failed"
        assert updated_data["error"] == error_message
    
    def test_mark_failed_sets_timestamp(self, job_manager, mock_redis):
        """Test that mark_failed sets completed_at timestamp."""
        job_id = "test-job-123"
        error_message = "Processing failed"
        
        # Mock existing job data
        existing_data = {
            "job_id": job_id,
            "status": "processing"
        }
        mock_redis.get.return_value = json.dumps(existing_data)
        
        job_manager.mark_failed(job_id, error_message)
        
        # Get the updated data
        call_args = mock_redis.setex.call_args
        updated_data = json.loads(call_args[0][2])
        
        assert "completed_at" in updated_data
        datetime.fromisoformat(updated_data["completed_at"])


class TestGetStatus:
    """Tests for get_status functionality."""
    
    def test_get_status_returns_job_data(self, job_manager, mock_redis):
        """Test that get_status returns complete job data."""
        job_id = "test-job-123"
        
        # Mock job data
        job_data = {
            "job_id": job_id,
            "status": "processing",
            "progress": {"current_page": 3, "total_pages": 10, "percentage": 30},
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:05:00"
        }
        mock_redis.get.return_value = json.dumps(job_data)
        
        result = job_manager.get_status(job_id)
        
        assert result["job_id"] == job_id
        assert result["status"] == "processing"
        assert result["progress"]["current_page"] == 3
        assert result["progress"]["total_pages"] == 10
    
    def test_get_status_raises_on_nonexistent_job(self, job_manager, mock_redis):
        """Test that get_status raises JobNotFoundError for nonexistent job."""
        job_id = "nonexistent-job"
        mock_redis.get.return_value = None
        
        with pytest.raises(JobNotFoundError) as exc_info:
            job_manager.get_status(job_id)
        
        assert job_id in str(exc_info.value)
    
    def test_get_status_includes_error_for_failed_jobs(self, job_manager, mock_redis):
        """Test that get_status includes error message for failed jobs."""
        job_id = "test-job-123"
        error_message = "Processing failed"
        
        # Mock failed job data
        job_data = {
            "job_id": job_id,
            "status": "failed",
            "error": error_message
        }
        mock_redis.get.return_value = json.dumps(job_data)
        
        result = job_manager.get_status(job_id)
        
        assert result["status"] == "failed"
        assert result["error"] == error_message
    
    def test_get_status_includes_output_path_for_completed_jobs(self, job_manager, mock_redis):
        """Test that get_status includes output_path for completed jobs."""
        job_id = "test-job-123"
        output_path = "/uploads/test-job-123/output.docx"
        
        # Mock completed job data
        job_data = {
            "job_id": job_id,
            "status": "completed",
            "output_path": output_path
        }
        mock_redis.get.return_value = json.dumps(job_data)
        
        result = job_manager.get_status(job_id)
        
        assert result["status"] == "completed"
        assert result["output_path"] == output_path


class TestRedisKeyManagement:
    """Tests for Redis key management."""
    
    def test_job_key_format(self, job_manager):
        """Test that job keys follow the correct format."""
        job_id = "test-job-123"
        
        key = job_manager._get_job_key(job_id)
        
        assert key == f"job:{job_id}"
    
    def test_different_jobs_have_different_keys(self, job_manager):
        """Test that different job IDs produce different keys."""
        job_id_1 = "job-1"
        job_id_2 = "job-2"
        
        key_1 = job_manager._get_job_key(job_id_1)
        key_2 = job_manager._get_job_key(job_id_2)
        
        assert key_1 != key_2
