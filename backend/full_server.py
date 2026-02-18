"""
Full Flask server with conversion (handles missing Tesseract gracefully).
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import uuid
from pathlib import Path
import traceback

app = Flask(__name__)
CORS(app)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

UPLOAD_FOLDER = Path("../uploads")
UPLOAD_FOLDER.mkdir(exist_ok=True)

jobs = {}

# Try to import conversion components
try:
    from app.pdf_converter import PDFConverter
    from app.file_manager import FileManager
    CONVERSION_AVAILABLE = True
    file_manager = FileManager()
    print("✓ Conversion components loaded successfully")
except Exception as e:
    CONVERSION_AVAILABLE = False
    print(f"✗ Conversion not available: {e}")

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        "status": "ok",
        "conversion_available": CONVERSION_AVAILABLE
    }), 200

@app.route('/api/upload', methods=['POST'])
def upload():
    try:
        print("\n" + "="*60)
        print("Upload request received")
        
        if 'file' not in request.files:
            return jsonify({"error": "No file"}), 400
        
        file = request.files['file']
        if not file.filename:
            return jsonify({"error": "No filename"}), 400
        
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({"error": "Not a PDF"}), 400
        
        job_id = str(uuid.uuid4())
        print(f"Job ID: {job_id}")
        
        # Save file
        if CONVERSION_AVAILABLE:
            file_path = file_manager.store_upload(file, job_id)
        else:
            job_dir = UPLOAD_FOLDER / job_id
            job_dir.mkdir(parents=True, exist_ok=True)
            file_path = job_dir / "input.pdf"
            file.save(str(file_path))
        
        print(f"File saved: {file_path}")
        
        # Initialize job
        jobs[job_id] = {
            "job_id": job_id,
            "status": "processing",
            "progress": {"current_page": 0, "total_pages": 0, "percentage": 0}
        }
        
        # Try conversion
        if CONVERSION_AVAILABLE:
            try:
                print("Starting conversion...")
                converter = PDFConverter()
                
                if CONVERSION_AVAILABLE:
                    output_path = str(Path(file_manager.upload_folder) / job_id / "output.docx")
                else:
                    output_path = str(UPLOAD_FOLDER / job_id / "output.docx")
                
                def progress_callback(current, total):
                    jobs[job_id]["progress"] = {
                        "current_page": current,
                        "total_pages": total,
                        "percentage": int((current / total) * 100) if total > 0 else 0
                    }
                    print(f"Progress: {current}/{total}")
                
                result = converter.convert(str(file_path), output_path, progress_callback)
                
                if result["success"]:
                    jobs[job_id]["status"] = "completed"
                    print("✓ Conversion completed successfully")
                else:
                    jobs[job_id]["status"] = "failed"
                    jobs[job_id]["error"] = "Conversion failed"
                    print("✗ Conversion failed")
                    
            except Exception as e:
                error_msg = str(e)
                print(f"✗ Conversion error: {error_msg}")
                traceback.print_exc()
                jobs[job_id]["status"] = "failed"
                jobs[job_id]["error"] = f"Conversion error: {error_msg}"
        else:
            jobs[job_id]["status"] = "failed"
            jobs[job_id]["error"] = "Conversion components not available. Please install dependencies."
        
        print("="*60 + "\n")
        
        return jsonify({
            "job_id": job_id,
            "status": jobs[job_id]["status"],
            "message": "File processed"
        }), 202
        
    except Exception as e:
        print(f"✗ Upload error: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/jobs/<job_id>', methods=['GET'])
def status(job_id):
    if job_id in jobs:
        return jsonify(jobs[job_id]), 200
    return jsonify({"error": "Job not found"}), 404

@app.route('/api/download/<job_id>', methods=['GET'])
def download(job_id):
    try:
        if job_id not in jobs:
            return jsonify({"error": "Job not found"}), 404
        
        if jobs[job_id]["status"] != "completed":
            return jsonify({"error": f"Job is {jobs[job_id]['status']}"}), 400
        
        if CONVERSION_AVAILABLE:
            output_path = file_manager.get_output_path(job_id)
        else:
            output_path = str(UPLOAD_FOLDER / job_id / "output.docx")
        
        if not output_path or not os.path.exists(output_path):
            return jsonify({"error": "File not found"}), 404
        
        return send_file(
            output_path,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            as_attachment=True,
            download_name=f"converted_{job_id}.docx"
        )
    except Exception as e:
        print(f"Download error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("\n" + "="*60)
    print("  PDF to Word Converter - Full Server")
    if CONVERSION_AVAILABLE:
        print("  ✓ Conversion: ENABLED")
    else:
        print("  ✗ Conversion: DISABLED (missing dependencies)")
    print("="*60 + "\n")
    app.run(host='0.0.0.0', port=5000, threaded=True)
