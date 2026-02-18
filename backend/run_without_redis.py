"""
Simple Flask server that processes conversions synchronously without Redis/Celery.
This is for testing purposes only - not for production use.
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import uuid
import logging
from pathlib import Path

from app.file_manager import FileManager
from app.pdf_converter import PDFConverter
from app.exceptions import FileUploadError, ConversionError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

file_manager = FileManager()

# In-memory job storage (for testing without Redis)
jobs = {}

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "service": "PDF to Word Converter API (No Redis Mode)"}), 200

@app.route('/api/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            raise FileUploadError("No file provided")
        
        file = request.files['file']
        if file.filename == '':
            raise FileUploadError("No file selected")
        
        if not file.filename.lower().endswith('.pdf'):
            raise FileUploadError("Only PDF files are accepted")
        
        job_id = str(uuid.uuid4())
        
        # Store file
        file_path = file_manager.store_upload(file, job_id)
        logger.info(f"File uploaded: {job_id}")
        
        # Initialize job
        jobs[job_id] = {
            "job_id": job_id,
            "status": "processing",
            "progress": {"current_page": 0, "total_pages": 0, "percentage": 0},
            "created_at": "2026-02-17T12:00:00Z"
        }
        
        # Process synchronously (blocking)
        try:
            converter = PDFConverter()
            output_path = os.path.join(file_manager.upload_folder, job_id, 'output.docx')
            
            def progress_callback(current, total):
                jobs[job_id]["progress"] = {
                    "current_page": current,
                    "total_pages": total,
                    "percentage": int((current / total) * 100)
                }
            
            result = converter.convert(file_path, output_path, progress_callback)
            
            if result["success"]:
                jobs[job_id]["status"] = "completed"
                jobs[job_id]["completed_at"] = "2026-02-17T12:00:00Z"
                logger.info(f"Conversion completed: {job_id}")
            else:
                jobs[job_id]["status"] = "failed"
                jobs[job_id]["error"] = "Conversion failed"
                
        except Exception as e:
            logger.error(f"Conversion error: {e}")
            jobs[job_id]["status"] = "failed"
            jobs[job_id]["error"] = str(e)
        
        return jsonify({
            "job_id": job_id,
            "status": jobs[job_id]["status"],
            "message": "File processed"
        }), 202
        
    except FileUploadError as e:
        return jsonify({"error": "File Upload Error", "message": str(e)}), 400
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return jsonify({"error": "Internal Server Error", "message": str(e)}), 500

@app.route('/api/jobs/<job_id>', methods=['GET'])
def get_job_status(job_id):
    if job_id not in jobs:
        return jsonify({"error": "Job Not Found", "message": f"Job {job_id} does not exist"}), 404
    return jsonify(jobs[job_id]), 200

@app.route('/api/download/<job_id>', methods=['GET'])
def download_file(job_id):
    if job_id not in jobs:
        return jsonify({"error": "Job Not Found"}), 404
    
    if jobs[job_id]["status"] != "completed":
        return jsonify({"error": "Job Not Ready", "message": f"Job is {jobs[job_id]['status']}"}), 400
    
    output_path = file_manager.get_output_path(job_id)
    if not output_path or not os.path.exists(output_path):
        return jsonify({"error": "File Not Found"}), 404
    
    return send_file(
        output_path,
        mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        as_attachment=True,
        download_name=f"converted_{job_id}.docx"
    )

if __name__ == '__main__':
    print("\n" + "="*60)
    print("  PDF to Word Converter - No Redis Mode")
    print("  WARNING: This is for testing only!")
    print("  Conversions will block the server.")
    print("="*60 + "\n")
    app.run(debug=False, host='0.0.0.0', port=5000, use_reloader=False)
