"""
Unit tests for FileManager component.

Tests file storage, retrieval, cleanup, and error handling.
"""

import os
import shutil
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from werkzeug.datastructures import FileStorage

from app.file_manager import FileManager
from app.exceptions import FileIOError, JobNotFoundError


@pytest.fixture
def temp_upload_folder():
    """Create a temporary upload folder for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup after test
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)


@pytest.fixture
def file_manager(temp_upload_folder):
    """Create a FileManager instance with temporary folder."""
    return FileManager(upload_folder=temp_upload_folder)


@pytest.fixture
def mock_file():
    """Create a mock FileStorage object."""
    mock = Mock(spec=FileStorage)
    mock.filename = "test_document.pdf"
    return mock


class TestFileManagerInitialization:
    """Test FileManager initialization."""
    
    def test_creates_upload_folder_if_not_exists(self, temp_upload_folder):
        """Test that FileManager creates upload folder on initialization."""
        # Remove the folder
        shutil.rmtree(temp_upload_folder)
        assert not os.path.exists(temp_upload_folder)
        
        # Initialize FileManager
        fm = FileManager(upload_folder=temp_upload_folder)
        
        # Folder should be created
        assert os.path.exists(temp_upload_folder)
        assert os.path.isdir(temp_upload_folder)
    
    def test_uses_existing_upload_folder(self, temp_upload_folder):
        """Test that FileManager works with existing folder."""
        # Folder already exists
        assert os.path.exists(temp_upload_folder)
        
        # Initialize FileManager
        fm = FileManager(upload_folder=temp_upload_folder)
        
        # Should not raise error
        assert fm.upload_folder == temp_upload_folder


class TestStoreUpload:
    """Test store_upload method."""
    
    def test_stores_file_with_job_id(self, file_manager, mock_file, temp_upload_folder):
        """Test storing an uploaded file creates correct directory structure."""
        job_id = "test-job-123"
        
        # Store the file
        file_path = file_manager.store_upload(mock_file, job_id)
        
        # Verify directory structure
        expected_dir = Path(temp_upload_folder) / job_id
        expected_file = expected_dir / "input.pdf"
        
        assert expected_dir.exists()
        assert expected_dir.is_dir()
        assert file_path == str(expected_file.absolute())
        
        # Verify save was called
        mock_file.save.assert_called_once_with(str(expected_file))
    
    def test_creates_job_directory(self, file_manager, mock_file, temp_upload_folder):
        """Test that job directory is created if it doesn't exist."""
        job_id = "new-job-456"
        job_dir = Path(temp_upload_folder) / job_id
        
        assert not job_dir.exists()
        
        file_manager.store_upload(mock_file, job_id)
        
        assert job_dir.exists()
        assert job_dir.is_dir()
    
    def test_raises_error_on_save_failure(self, file_manager, mock_file):
        """Test that FileIOError is raised when file save fails."""
        job_id = "error-job"
        mock_file.save.side_effect = IOError("Disk full")
        
        with pytest.raises(FileIOError) as exc_info:
            file_manager.store_upload(mock_file, job_id)
        
        assert "Failed to store uploaded file" in str(exc_info.value)
        assert exc_info.value.details["job_id"] == job_id


class TestStoreOutput:
    """Test store_output method."""
    
    def test_stores_output_file(self, file_manager, temp_upload_folder):
        """Test storing a converted output file."""
        job_id = "output-job-789"
        
        # Create a temporary source file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.docx', delete=False) as tmp:
            tmp.write("Test content")
            source_path = tmp.name
        
        try:
            # Store the output
            output_path = file_manager.store_output(source_path, job_id)
            
            # Verify directory structure
            expected_dir = Path(temp_upload_folder) / job_id
            expected_file = expected_dir / "output.docx"
            
            assert expected_dir.exists()
            assert expected_file.exists()
            assert output_path == str(expected_file.absolute())
            
            # Verify content was copied
            with open(expected_file, 'r') as f:
                assert f.read() == "Test content"
        
        finally:
            # Cleanup source file
            if os.path.exists(source_path):
                os.unlink(source_path)
    
    def test_creates_job_directory_for_output(self, file_manager, temp_upload_folder):
        """Test that job directory is created when storing output."""
        job_id = "new-output-job"
        job_dir = Path(temp_upload_folder) / job_id
        
        # Create temporary source file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.docx', delete=False) as tmp:
            tmp.write("Content")
            source_path = tmp.name
        
        try:
            assert not job_dir.exists()
            
            file_manager.store_output(source_path, job_id)
            
            assert job_dir.exists()
        
        finally:
            if os.path.exists(source_path):
                os.unlink(source_path)
    
    def test_raises_error_on_copy_failure(self, file_manager):
        """Test that FileIOError is raised when file copy fails."""
        job_id = "copy-error-job"
        non_existent_path = "/non/existent/file.docx"
        
        with pytest.raises(FileIOError) as exc_info:
            file_manager.store_output(non_existent_path, job_id)
        
        assert "Failed to store output file" in str(exc_info.value)
        assert exc_info.value.details["job_id"] == job_id


class TestGetOutputPath:
    """Test get_output_path method."""
    
    def test_returns_path_when_file_exists(self, file_manager, temp_upload_folder):
        """Test retrieving output path for existing file."""
        job_id = "existing-job"
        job_dir = Path(temp_upload_folder) / job_id
        job_dir.mkdir(parents=True)
        
        # Create output file
        output_file = job_dir / "output.docx"
        output_file.write_text("Test output")
        
        # Get path
        result = file_manager.get_output_path(job_id)
        
        assert result == str(output_file.absolute())
    
    def test_returns_none_when_file_not_exists(self, file_manager):
        """Test that None is returned when output file doesn't exist."""
        job_id = "non-existent-job"
        
        result = file_manager.get_output_path(job_id)
        
        assert result is None
    
    def test_returns_none_when_directory_not_exists(self, file_manager):
        """Test that None is returned when job directory doesn't exist."""
        job_id = "no-directory-job"
        
        result = file_manager.get_output_path(job_id)
        
        assert result is None


class TestGetInputPath:
    """Test get_input_path method."""
    
    def test_returns_path_when_file_exists(self, file_manager, temp_upload_folder):
        """Test retrieving input path for existing file."""
        job_id = "input-job"
        job_dir = Path(temp_upload_folder) / job_id
        job_dir.mkdir(parents=True)
        
        # Create input file
        input_file = job_dir / "input.pdf"
        input_file.write_text("Test PDF")
        
        # Get path
        result = file_manager.get_input_path(job_id)
        
        assert result == str(input_file.absolute())
    
    def test_returns_none_when_file_not_exists(self, file_manager):
        """Test that None is returned when input file doesn't exist."""
        job_id = "no-input-job"
        
        result = file_manager.get_input_path(job_id)
        
        assert result is None


class TestCleanupOldFiles:
    """Test cleanup_old_files method."""
    
    def test_deletes_old_directories(self, file_manager, temp_upload_folder):
        """Test that directories older than max_age are deleted."""
        # Create old job directory
        old_job_id = "old-job"
        old_job_dir = Path(temp_upload_folder) / old_job_id
        old_job_dir.mkdir(parents=True)
        (old_job_dir / "input.pdf").write_text("Old file")
        
        # Set modification time to 25 hours ago
        old_time = time.time() - (25 * 3600)
        os.utime(old_job_dir, (old_time, old_time))
        
        # Create recent job directory
        new_job_id = "new-job"
        new_job_dir = Path(temp_upload_folder) / new_job_id
        new_job_dir.mkdir(parents=True)
        (new_job_dir / "input.pdf").write_text("New file")
        
        # Run cleanup with 24 hour threshold
        deleted_count = file_manager.cleanup_old_files(max_age_hours=24)
        
        # Old directory should be deleted
        assert not old_job_dir.exists()
        # New directory should remain
        assert new_job_dir.exists()
        # Should report 1 deletion
        assert deleted_count == 1
    
    def test_keeps_recent_directories(self, file_manager, temp_upload_folder):
        """Test that recent directories are not deleted."""
        # Create recent job directory
        job_id = "recent-job"
        job_dir = Path(temp_upload_folder) / job_id
        job_dir.mkdir(parents=True)
        (job_dir / "input.pdf").write_text("Recent file")
        
        # Run cleanup
        deleted_count = file_manager.cleanup_old_files(max_age_hours=24)
        
        # Directory should still exist
        assert job_dir.exists()
        assert deleted_count == 0
    
    def test_returns_zero_when_no_files_to_delete(self, file_manager):
        """Test that cleanup returns 0 when no old files exist."""
        deleted_count = file_manager.cleanup_old_files(max_age_hours=24)
        
        assert deleted_count == 0
    
    def test_handles_non_existent_upload_folder(self, temp_upload_folder):
        """Test cleanup handles non-existent upload folder gracefully."""
        # Remove upload folder
        shutil.rmtree(temp_upload_folder)
        
        fm = FileManager(upload_folder=temp_upload_folder + "_nonexistent")
        deleted_count = fm.cleanup_old_files(max_age_hours=24)
        
        assert deleted_count == 0


class TestDeleteJobFiles:
    """Test delete_job_files method."""
    
    def test_deletes_job_directory(self, file_manager, temp_upload_folder):
        """Test that entire job directory is deleted."""
        job_id = "delete-job"
        job_dir = Path(temp_upload_folder) / job_id
        job_dir.mkdir(parents=True)
        (job_dir / "input.pdf").write_text("Input")
        (job_dir / "output.docx").write_text("Output")
        
        assert job_dir.exists()
        
        file_manager.delete_job_files(job_id)
        
        assert not job_dir.exists()
    
    def test_raises_error_when_job_not_found(self, file_manager):
        """Test that JobNotFoundError is raised for non-existent job."""
        job_id = "non-existent-job"
        
        with pytest.raises(JobNotFoundError) as exc_info:
            file_manager.delete_job_files(job_id)
        
        assert "Job directory not found" in str(exc_info.value)
        assert exc_info.value.details["job_id"] == job_id


class TestFilenameSanitization:
    """Test filename sanitization."""
    
    def test_sanitizes_dangerous_filenames(self, file_manager):
        """Test that dangerous characters are removed from filenames."""
        dangerous_names = [
            "../../../etc/passwd",
            "file<>name.pdf",
            "file|name.pdf",
            "file:name.pdf",
        ]
        
        for name in dangerous_names:
            sanitized = file_manager._sanitize_filename(name)
            # Should not contain path traversal or special characters
            assert ".." not in sanitized
            assert "/" not in sanitized
            assert "\\" not in sanitized
            assert "<" not in sanitized
            assert ">" not in sanitized
            assert "|" not in sanitized
            assert ":" not in sanitized
    
    def test_preserves_safe_filenames(self, file_manager):
        """Test that safe filenames are preserved."""
        safe_name = "my_document-2024.pdf"
        sanitized = file_manager._sanitize_filename(safe_name)
        
        # Should be similar to original (secure_filename may change it slightly)
        assert "my_document" in sanitized
        assert "2024" in sanitized
        assert ".pdf" in sanitized
    
    def test_handles_empty_filename(self, file_manager):
        """Test that empty filename is handled."""
        sanitized = file_manager._sanitize_filename("")
        
        # Should return a default filename
        assert sanitized == "file"


class TestGetOriginalFilename:
    """Test get_original_filename method."""
    
    def test_returns_filename_when_output_exists(self, file_manager, temp_upload_folder):
        """Test that filename is returned when output exists."""
        job_id = "filename-job"
        job_dir = Path(temp_upload_folder) / job_id
        job_dir.mkdir(parents=True)
        (job_dir / "output.docx").write_text("Output")
        
        filename = file_manager.get_original_filename(job_id)
        
        assert filename is not None
        assert filename.endswith(".docx")
        assert job_id in filename
    
    def test_returns_none_when_output_not_exists(self, file_manager):
        """Test that None is returned when output doesn't exist."""
        job_id = "no-output-job"
        
        filename = file_manager.get_original_filename(job_id)
        
        assert filename is None
