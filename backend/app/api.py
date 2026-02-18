"""
Flask REST API for PDF to Word conversion service.

This module provides HTTP endpoints for file upload, job status tracking,
and file download.
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
import os
import logging

from app.file_manager import FileManager
from app.job_manager import JobManager
from app.redis_client import RedisClient, get_redis_client
from app.tasks import convert_pdf_task
from app.exceptions import (
    ConversionError,
    FileUploadError,
    JobNotFoundError,
    FileIOError
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app(config=None):
    """
    Create and configure the Flask application.
    
    Args:
        config: Configuration object (optional)
        
    Returns:
        Flask application instance
    """
    app = Flask(__name__)
    
    # Load configuration
    if config:
        app.config.from_object(config)
        app_config = config
    else:
        from app.config import get_config
        app_config = get_config()
        app.config.from_object(app_config)
    
    # Configure CORS
    # In production, restrict origins to specific domains
    CORS(app, resources={
        r"/api/*": {
            "origins": "*",  # Change to specific origins in production
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type"]
        }
    })
    
    # Set maximum file upload size (50MB)
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB in bytes
    
    # Initialize Redis client
    redis_client = RedisClient()
    redis_client.initialize(app_config)
    
    # Initialize managers
    file_manager = FileManager()
    job_manager = JobManager(redis_client.get_client())
    
    # Error handlers
    @app.errorhandler(400)
    def bad_request(error):
        """Handle 400 Bad Request errors."""
        return jsonify({
            "error": "Bad Request",
            "message": str(error)
        }), 400
    
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 Not Found errors."""
        return jsonify({
            "error": "Not Found",
            "message": "The requested resource was not found"
        }), 404
    
    @app.errorhandler(413)
    def request_entity_too_large(error):
        """Handle 413 Request Entity Too Large errors."""
        return jsonify({
            "error": "File Too Large",
            "message": "File size exceeds maximum allowed size of 50MB"
        }), 413
    
    @app.errorhandler(500)
    def internal_server_error(error):
        """Handle 500 Internal Server Error."""
        logger.error(f"Internal server error: {error}", exc_info=True)
        return jsonify({
            "error": "Internal Server Error",
            "message": "An unexpected error occurred"
        }), 500
    
    # API Routes
    
    @app.route('/api/health', methods=['GET'])
    def health_check():
        """
        Health check endpoint.
        
        Returns:
            JSON response with service status
        """
        return jsonify({
            "status": "healthy",
            "service": "PDF to Word Converter API"
        }), 200
    
    @app.route('/api/upload', methods=['POST'])
    def upload_file():
        """
        Upload a PDF file for conversion.
        
        Accepts multipart/form-data with a 'file' field containing the PDF.
        Validates file type and size, stores the file, creates a job,
        and queues the conversion task.
        
        Returns:
            JSON response with job_id and status
            
        Requirements:
            - 9.3: Validate file type and size
            - 9.4: Accept PDF files up to 50MB
            - 9.5: Return error for invalid file types
            - 9.6: Return unique job identifier
            - 13.1: Queue conversion task
        """
        try:
            # Check if file is present in request
            if 'file' not in request.files:
                raise FileUploadError("No file provided in request")
            
            file = request.files['file']
            
            # Check if filename is empty
            if file.filename == '':
                raise FileUploadError("No file selected")
            
            # Validate file type (must be PDF)
            if not file.filename.lower().endswith('.pdf'):
                raise FileUploadError("Invalid file type. Only PDF files are accepted")
            
            # Secure the filename
            filename = secure_filename(file.filename)
            
            # Create the job first to get a unique job ID
            try:
                job_id = job_manager.create_job(filename)
                logger.info(f"Created job {job_id} for file {filename}")
            except Exception as e:
                raise ConversionError(f"Failed to create job: {str(e)}")
            
            # Store the uploaded file using the job_id
            try:
                file_path = file_manager.store_upload(file, job_id)
                logger.info(f"Stored file for job {job_id} at {file_path}")
            except Exception as e:
                # Clean up job if file storage fails
                try:
                    job_manager.mark_failed(job_id, f"File storage failed: {str(e)}")
                except:
                    pass
                raise FileUploadError(f"Failed to store uploaded file: {str(e)}")
            
            # Queue the conversion task
            try:
                convert_pdf_task.delay(job_id)
                logger.info(f"Queued conversion task for job {job_id}")
            except Exception as e:
                # Clean up if task queueing fails
                job_manager.mark_failed(job_id, f"Task queueing failed: {str(e)}")
                file_manager.delete_job_files(job_id)
                raise ConversionError(f"Failed to queue conversion task: {str(e)}")
            
            # Return job response
            return jsonify({
                "job_id": job_id,
                "status": "pending",
                "message": "File uploaded successfully. Conversion queued."
            }), 202  # 202 Accepted
            
        except FileUploadError as e:
            logger.warning(f"File upload error: {e}")
            return jsonify({
                "error": "File Upload Error",
                "message": str(e)
            }), 400
            
        except ConversionError as e:
            logger.error(f"Conversion error: {e}")
            return jsonify({
                "error": "Conversion Error",
                "message": str(e)
            }), 500
            
        except Exception as e:
            logger.error(f"Unexpected error during upload: {e}", exc_info=True)
            return jsonify({
                "error": "Internal Server Error",
                "message": "An unexpected error occurred during file upload"
            }), 500
    
    @app.route('/api/jobs/<job_id>', methods=['GET'])
    def get_job_status(job_id):
        """
        Get the status of a conversion job.
        
        Args:
            job_id: Unique job identifier
            
        Returns:
            JSON response with job status and progress information
            
        Requirements:
            - 11.1: Return current progress information
            - 12.5: Return 404 for non-existent jobs
            - 13.2: Provide job status endpoint
        """
        try:
            # Get job status from JobManager
            status = job_manager.get_status(job_id)
            
            return jsonify(status), 200
            
        except JobNotFoundError as e:
            logger.warning(f"Job not found: {job_id}")
            return jsonify({
                "error": "Job Not Found",
                "message": f"Job {job_id} does not exist"
            }), 404
            
        except Exception as e:
            logger.error(f"Error retrieving job status: {e}", exc_info=True)
            return jsonify({
                "error": "Internal Server Error",
                "message": "Failed to retrieve job status"
            }), 500
    
    @app.route('/api/download/<job_id>', methods=['GET'])
    def download_file(job_id):
        """
        Download the converted Word document.
        
        Args:
            job_id: Unique job identifier
            
        Returns:
            Word document file or error response
            
        Requirements:
            - 12.2: Serve Word document for download
            - 12.3: Provide original filename with .docx extension
            - 12.5: Return 404 for non-existent or incomplete jobs
            - 13.3: Download endpoint
        """
        try:
            # Check if job exists and is completed
            try:
                status = job_manager.get_status(job_id)
            except JobNotFoundError:
                return jsonify({
                    "error": "Job Not Found",
                    "message": f"Job {job_id} does not exist"
                }), 404
            
            # Check if job is completed
            if status['status'] != 'completed':
                return jsonify({
                    "error": "Job Not Ready",
                    "message": f"Job is {status['status']}. File is not ready for download."
                }), 400
            
            # Get output file path
            output_path = file_manager.get_output_path(job_id)
            
            if not output_path or not os.path.exists(output_path):
                return jsonify({
                    "error": "File Not Found",
                    "message": "Converted file not found or has been deleted"
                }), 404
            
            # Get original filename
            original_filename = file_manager.get_original_filename(job_id)
            if original_filename:
                # Replace .pdf extension with .docx
                download_name = original_filename.rsplit('.', 1)[0] + '.docx'
            else:
                download_name = f"converted_{job_id}.docx"
            
            # Send file
            return send_file(
                output_path,
                mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                as_attachment=True,
                download_name=download_name
            )
            
        except Exception as e:
            logger.error(f"Error downloading file: {e}", exc_info=True)
            return jsonify({
                "error": "Internal Server Error",
                "message": "Failed to download file"
            }), 500
    
    return app


# Create the default app instance
app = create_app()


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
