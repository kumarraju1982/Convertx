"""
Celery tasks for PDF to Word conversion.

This module defines asynchronous tasks for processing PDF conversions,
including progress tracking and error handling.
"""

from celery import Task
from app.celery_app import celery_app
from app.pdf_converter import PDFConverter
from app.job_manager import JobManager
from app.file_manager import FileManager
from app.redis_client import get_redis_client
from app.exceptions import ConversionError, PDFValidationError
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConversionTask(Task):
    """
    Base task class for conversion tasks with automatic retry logic.
    """
    autoretry_for = (ConnectionError, TimeoutError)
    retry_kwargs = {'max_retries': 3}
    retry_backoff = True
    retry_backoff_max = 600  # 10 minutes
    retry_jitter = True


@celery_app.task(bind=True, base=ConversionTask, name='app.tasks.convert_pdf_task')
def convert_pdf_task(self, job_id: str) -> dict:
    """
    Celery task to convert a PDF file to Word document.
    
    This task orchestrates the full conversion pipeline:
    1. Retrieve input file path from FileManager
    2. Update job status to "processing"
    3. Run conversion with progress callbacks
    4. Store output file
    5. Update job status to "completed" or "failed"
    
    Args:
        self: Task instance (bound)
        job_id: Unique job identifier
        
    Returns:
        Dictionary with task result:
        {
            "success": bool,
            "job_id": str,
            "output_path": str | None,
            "pages_processed": int,
            "pages_failed": List[int],
            "errors": List[str]
        }
        
    Requirements:
        - 10.1: Use Redis for job state storage
        - 10.3: Update job status to "processing" when task starts
        - 10.4: Update job status to "completed" when done
        - 10.5: Update job status to "failed" on error
        - 10.6: Update progress during conversion
        - 12.1: Store output file using FileManager
    """
    # Initialize components
    from app.redis_client import RedisClient
    from app.config import get_config
    
    redis_client = RedisClient()
    redis_client.initialize(get_config())
    redis_conn = redis_client.get_client()
    
    job_manager = JobManager(redis_conn)
    file_manager = FileManager()
    converter = PDFConverter()
    
    try:
        logger.info(f"Starting conversion for job {job_id}")
        
        # Get input file path
        input_path = file_manager.get_input_path(job_id)
        if not input_path:
            raise ConversionError(f"Input file not found for job {job_id}")
        
        # Update job status to processing
        job_manager.mark_processing(job_id)
        logger.info(f"Job {job_id} marked as processing")
        
        # Define progress callback
        def progress_callback(current_page: int, total_pages: int):
            """Update job progress in Redis."""
            try:
                job_manager.update_progress(job_id, current_page, total_pages)
                logger.info(f"Job {job_id}: Processing page {current_page}/{total_pages}")
                
                # Update Celery task state for monitoring (only if task_id exists)
                if self.request.id:
                    self.update_state(
                        state='PROGRESS',
                        meta={
                            'current': current_page,
                            'total': total_pages,
                            'percentage': int((current_page / total_pages) * 100)
                        }
                    )
            except Exception as e:
                logger.error(f"Error updating progress for job {job_id}: {e}")
        
        # Determine output path
        output_path = file_manager.get_output_path(job_id)
        if not output_path:
            # Generate output path if not exists
            import os
            job_dir = os.path.join(file_manager.upload_folder, job_id)
            output_path = os.path.join(job_dir, 'output.docx')
        
        # Run conversion
        logger.info(f"Starting PDF conversion for job {job_id}")
        result = converter.convert(
            pdf_path=input_path,
            output_path=output_path,
            progress_callback=progress_callback
        )
        
        if result["success"]:
            # Store output file (already saved by converter, just verify)
            if file_manager.get_output_path(job_id):
                # Mark job as completed
                job_manager.mark_completed(job_id, output_path)
                logger.info(f"Job {job_id} completed successfully")
                
                return {
                    "success": True,
                    "job_id": job_id,
                    "output_path": output_path,
                    "pages_processed": result["pages_processed"],
                    "pages_failed": result["pages_failed"],
                    "errors": result["errors"]
                }
            else:
                raise ConversionError("Output file was not created")
        else:
            raise ConversionError("Conversion failed")
            
    except PDFValidationError as e:
        # PDF validation errors (non-retryable)
        error_msg = f"PDF validation failed: {str(e)}"
        logger.error(f"Job {job_id}: {error_msg}")
        job_manager.mark_failed(job_id, error_msg)
        
        return {
            "success": False,
            "job_id": job_id,
            "output_path": None,
            "pages_processed": 0,
            "pages_failed": [],
            "errors": [error_msg]
        }
        
    except ConversionError as e:
        # Conversion errors (non-retryable)
        error_msg = f"Conversion error: {str(e)}"
        logger.error(f"Job {job_id}: {error_msg}")
        job_manager.mark_failed(job_id, error_msg)
        
        return {
            "success": False,
            "job_id": job_id,
            "output_path": None,
            "pages_processed": 0,
            "pages_failed": [],
            "errors": [error_msg]
        }
        
    except Exception as e:
        # Unexpected errors (may be retryable)
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(f"Job {job_id}: {error_msg}", exc_info=True)
        
        # Check if we should retry
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying job {job_id} (attempt {self.request.retries + 1}/{self.max_retries})")
            raise self.retry(exc=e)
        else:
            # Max retries reached, mark as failed
            job_manager.mark_failed(job_id, error_msg)
            
            return {
                "success": False,
                "job_id": job_id,
                "output_path": None,
                "pages_processed": 0,
                "pages_failed": [],
                "errors": [error_msg]
            }


@celery_app.task(name='app.tasks.cleanup_old_files_task')
def cleanup_old_files_task(max_age_hours: int = 24) -> dict:
    """
    Celery periodic task to clean up old files.
    
    This task runs periodically (e.g., every hour) to delete files
    that are older than the specified age.
    
    Args:
        max_age_hours: Maximum age of files in hours (default: 24)
        
    Returns:
        Dictionary with cleanup result:
        {
            "success": bool,
            "files_deleted": int,
            "errors": List[str]
        }
        
    Requirements:
        - 12.4: Delete files older than 24 hours
    """
    file_manager = FileManager()
    
    try:
        logger.info(f"Starting cleanup of files older than {max_age_hours} hours")
        
        files_deleted = file_manager.cleanup_old_files(max_age_hours)
        
        logger.info(f"Cleanup completed: {files_deleted} files deleted")
        
        return {
            "success": True,
            "files_deleted": files_deleted,
            "errors": []
        }
        
    except Exception as e:
        error_msg = f"Cleanup failed: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        return {
            "success": False,
            "files_deleted": 0,
            "errors": [error_msg]
        }
