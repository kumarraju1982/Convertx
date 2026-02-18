"""
File Manager component for handling file storage, retrieval, and cleanup.

This module manages the file system operations for uploaded PDFs and converted
Word documents, organizing them by job ID and providing cleanup functionality.
"""

import os
import re
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from .config import Config
from .exceptions import FileIOError, JobNotFoundError


class FileManager:
    """
    Manages file storage and retrieval for conversion jobs.
    
    Organizes files in a directory structure:
        uploads/{job_id}/input.pdf
        uploads/{job_id}/output.docx
    """
    
    def __init__(self, upload_folder: str = None):
        """
        Initialize FileManager.
        
        Args:
            upload_folder: Base directory for file storage (defaults to Config.UPLOAD_FOLDER)
        """
        self.upload_folder = upload_folder or Config.UPLOAD_FOLDER
        self._ensure_upload_folder_exists()
    
    def _ensure_upload_folder_exists(self) -> None:
        """Create the upload folder if it doesn't exist."""
        Path(self.upload_folder).mkdir(parents=True, exist_ok=True)
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename to prevent path traversal attacks.
        
        Args:
            filename: Original filename
            
        Returns:
            str: Sanitized filename safe for file system operations
        """
        # Use werkzeug's secure_filename for basic sanitization
        safe_name = secure_filename(filename)
        
        # Additional sanitization: remove any remaining problematic characters
        safe_name = re.sub(r'[^\w\s\-\.]', '', safe_name)
        
        # Ensure filename is not empty after sanitization
        if not safe_name:
            safe_name = "file"
        
        return safe_name
    
    def _get_job_directory(self, job_id: str) -> Path:
        """
        Get the directory path for a specific job.
        
        Args:
            job_id: Unique job identifier
            
        Returns:
            Path: Directory path for the job
        """
        return Path(self.upload_folder) / job_id
    
    def store_upload(self, file: FileStorage, job_id: str) -> str:
        """
        Save an uploaded file with the given job ID.
        
        Args:
            file: FileStorage object from Flask request
            job_id: Unique job identifier
            
        Returns:
            str: Absolute path to the stored file
            
        Raises:
            FileIOError: If file storage fails
        """
        try:
            # Create job directory
            job_dir = self._get_job_directory(job_id)
            job_dir.mkdir(parents=True, exist_ok=True)
            
            # Store file as input.pdf
            file_path = job_dir / "input.pdf"
            file.save(str(file_path))
            
            return str(file_path.absolute())
        
        except Exception as e:
            raise FileIOError(
                f"Failed to store uploaded file for job {job_id}",
                details={"job_id": job_id, "error": str(e)}
            )
    
    def store_output(self, file_path: str, job_id: str) -> str:
        """
        Save a converted output file with the given job ID.
        
        Args:
            file_path: Path to the converted file
            job_id: Unique job identifier
            
        Returns:
            str: Absolute path to the stored output file
            
        Raises:
            FileIOError: If file storage fails
        """
        try:
            # Get job directory
            job_dir = self._get_job_directory(job_id)
            job_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy file to output.docx
            output_path = job_dir / "output.docx"
            shutil.copy2(file_path, output_path)
            
            return str(output_path.absolute())
        
        except Exception as e:
            raise FileIOError(
                f"Failed to store output file for job {job_id}",
                details={"job_id": job_id, "source_path": file_path, "error": str(e)}
            )
    
    def get_output_path(self, job_id: str) -> Optional[str]:
        """
        Retrieve the output file path for a given job ID.
        
        Args:
            job_id: Unique job identifier
            
        Returns:
            str: Absolute path to the output file, or None if not found
        """
        output_path = self._get_job_directory(job_id) / "output.docx"
        
        if output_path.exists():
            return str(output_path.absolute())
        
        return None
    
    def get_input_path(self, job_id: str) -> Optional[str]:
        """
        Retrieve the input file path for a given job ID.
        
        Args:
            job_id: Unique job identifier
            
        Returns:
            str: Absolute path to the input file, or None if not found
        """
        input_path = self._get_job_directory(job_id) / "input.pdf"
        
        if input_path.exists():
            return str(input_path.absolute())
        
        return None
    
    def cleanup_old_files(self, max_age_hours: int = 24) -> int:
        """
        Delete files older than the specified age.
        
        Args:
            max_age_hours: Maximum age of files in hours (default: 24)
            
        Returns:
            int: Number of job directories deleted
        """
        deleted_count = 0
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        upload_path = Path(self.upload_folder)
        
        if not upload_path.exists():
            return 0
        
        # Iterate through job directories
        for job_dir in upload_path.iterdir():
            if not job_dir.is_dir():
                continue
            
            try:
                # Check directory modification time
                dir_mtime = datetime.fromtimestamp(job_dir.stat().st_mtime)
                
                if dir_mtime < cutoff_time:
                    # Delete the entire job directory
                    shutil.rmtree(job_dir)
                    deleted_count += 1
            
            except Exception as e:
                # Log error but continue with other directories
                print(f"Error cleaning up directory {job_dir}: {e}")
                continue
        
        return deleted_count
    
    def delete_job_files(self, job_id: str) -> None:
        """
        Delete all files associated with a specific job.
        
        Args:
            job_id: Unique job identifier
            
        Raises:
            JobNotFoundError: If job directory doesn't exist
        """
        job_dir = self._get_job_directory(job_id)
        
        if not job_dir.exists():
            raise JobNotFoundError(
                f"Job directory not found for job {job_id}",
                details={"job_id": job_id}
            )
        
        try:
            shutil.rmtree(job_dir)
        except Exception as e:
            raise FileIOError(
                f"Failed to delete files for job {job_id}",
                details={"job_id": job_id, "error": str(e)}
            )
    
    def get_original_filename(self, job_id: str) -> Optional[str]:
        """
        Get the original filename for a job (for download purposes).
        
        Since we store files as input.pdf, we'll return a generic name.
        In a real implementation, you might store the original filename in metadata.
        
        Args:
            job_id: Unique job identifier
            
        Returns:
            str: Original filename with .docx extension, or None if not found
        """
        # For now, return a generic filename based on job_id
        # In production, you'd store the original filename in Redis/database
        output_path = self.get_output_path(job_id)
        
        if output_path:
            return f"converted_{job_id}.docx"
        
        return None
