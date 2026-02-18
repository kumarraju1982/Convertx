"""
Job Manager module for managing conversion job state.

This module provides the JobManager class for creating jobs, tracking progress,
and managing job state transitions using Redis as the storage backend.
"""

import uuid
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from redis import Redis
from app.redis_client import get_redis_client
from app.exceptions import JobNotFoundError


class JobManager:
    """
    Manages conversion job state using Redis.
    
    This class handles job creation, progress tracking, and state transitions
    for PDF to Word conversion jobs. All job data is stored in Redis with
    appropriate expiration times.
    """
    
    # Redis key prefixes
    JOB_KEY_PREFIX = "job:"
    JOB_EXPIRATION_SECONDS = 86400 * 2  # 2 days
    
    def __init__(self, redis_client: Optional[Redis] = None):
        """
        Initialize JobManager.
        
        Args:
            redis_client: Optional Redis client instance. If not provided,
                         uses the default client from get_redis_client()
        """
        self._redis = redis_client or get_redis_client()
    
    def create_job(self, file_path: str) -> str:
        """
        Create a new conversion job with a unique ID.
        
        Args:
            file_path: Path to the uploaded PDF file
            
        Returns:
            str: Unique job identifier (UUID)
        """
        job_id = str(uuid.uuid4())
        
        job_data = {
            "job_id": job_id,
            "status": "pending",
            "file_path": file_path,
            "progress": {
                "current_page": 0,
                "total_pages": 0,
                "percentage": 0
            },
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Store job data in Redis
        key = self._get_job_key(job_id)
        self._redis.setex(
            key,
            self.JOB_EXPIRATION_SECONDS,
            json.dumps(job_data)
        )
        
        return job_id
    
    def update_progress(self, job_id: str, current_page: int, total_pages: int) -> None:
        """
        Update job progress with current and total page counts.
        
        Args:
            job_id: Job identifier
            current_page: Current page being processed (1-indexed)
            total_pages: Total number of pages in the document
            
        Raises:
            JobNotFoundError: If job_id does not exist
        """
        job_data = self._get_job_data(job_id)
        
        # Calculate percentage
        percentage = 0
        if total_pages > 0:
            percentage = int((current_page / total_pages) * 100)
        
        # Update progress information
        job_data["progress"] = {
            "current_page": current_page,
            "total_pages": total_pages,
            "percentage": percentage
        }
        job_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        # Save updated job data
        self._save_job_data(job_id, job_data)
    
    def mark_completed(self, job_id: str, output_path: str) -> None:
        """
        Mark a job as completed with the output file path.
        
        Args:
            job_id: Job identifier
            output_path: Path to the generated Word document
            
        Raises:
            JobNotFoundError: If job_id does not exist
        """
        job_data = self._get_job_data(job_id)
        
        job_data["status"] = "completed"
        job_data["output_path"] = output_path
        job_data["completed_at"] = datetime.now(timezone.utc).isoformat()
        job_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        # Set progress to 100%
        if job_data.get("progress"):
            job_data["progress"]["percentage"] = 100
            job_data["progress"]["current_page"] = job_data["progress"]["total_pages"]
        
        self._save_job_data(job_id, job_data)
    
    def mark_failed(self, job_id: str, error: str) -> None:
        """
        Mark a job as failed with an error message.
        
        Args:
            job_id: Job identifier
            error: Error message describing the failure
            
        Raises:
            JobNotFoundError: If job_id does not exist
        """
        job_data = self._get_job_data(job_id)
        
        job_data["status"] = "failed"
        job_data["error"] = error
        job_data["completed_at"] = datetime.now(timezone.utc).isoformat()
        job_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        self._save_job_data(job_id, job_data)
    
    def get_status(self, job_id: str) -> Dict[str, Any]:
        """
        Retrieve the current status of a job.
        
        Args:
            job_id: Job identifier
            
        Returns:
            dict: Job status information including:
                - job_id: Job identifier
                - status: Current status (pending/processing/completed/failed)
                - progress: Progress information (current_page, total_pages, percentage)
                - error: Error message (if status is failed)
                - created_at: Job creation timestamp
                - completed_at: Job completion timestamp (if completed or failed)
                - output_path: Output file path (if completed)
                
        Raises:
            JobNotFoundError: If job_id does not exist
        """
        return self._get_job_data(job_id)
    
    def mark_processing(self, job_id: str) -> None:
        """
        Mark a job as processing (worker has picked it up).
        
        Args:
            job_id: Job identifier
            
        Raises:
            JobNotFoundError: If job_id does not exist
        """
        job_data = self._get_job_data(job_id)
        
        job_data["status"] = "processing"
        job_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        self._save_job_data(job_id, job_data)
    
    def _get_job_key(self, job_id: str) -> str:
        """
        Get the Redis key for a job.
        
        Args:
            job_id: Job identifier
            
        Returns:
            str: Redis key
        """
        return f"{self.JOB_KEY_PREFIX}{job_id}"
    
    def _get_job_data(self, job_id: str) -> Dict[str, Any]:
        """
        Retrieve job data from Redis.
        
        Args:
            job_id: Job identifier
            
        Returns:
            dict: Job data
            
        Raises:
            JobNotFoundError: If job_id does not exist
        """
        key = self._get_job_key(job_id)
        data = self._redis.get(key)
        
        if data is None:
            raise JobNotFoundError(
                f"Job not found: {job_id}",
                details={"job_id": job_id}
            )
        
        return json.loads(data)
    
    def _save_job_data(self, job_id: str, job_data: Dict[str, Any]) -> None:
        """
        Save job data to Redis.
        
        Args:
            job_id: Job identifier
            job_data: Job data dictionary
        """
        key = self._get_job_key(job_id)
        self._redis.setex(
            key,
            self.JOB_EXPIRATION_SECONDS,
            json.dumps(job_data)
        )
