"""
Ultra-simple Flask server for testing uploads only.
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import uuid
from pathlib import Path

app = Flask(__name__)
CORS(app)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

UPLOAD_FOLDER = Path("../uploads")
UPLOAD_FOLDER.mkdir(exist_ok=True)

jobs = {}

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"}), 200

@app.route('/api/upload', methods=['POST'])
def upload():
    try:
        print("Upload request received")
        
        if 'file' not in request.files:
            return jsonify({"error": "No file"}), 400
        
        file = request.files['file']
        if not file.filename:
            return jsonify({"error": "No filename"}), 400
        
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({"error": "Not a PDF"}), 400
        
        job_id = str(uuid.uuid4())
        job_dir = UPLOAD_FOLDER / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = job_dir / "input.pdf"
        file.save(str(file_path))
        
        print(f"File saved: {job_id}")
        
        jobs[job_id] = {
            "job_id": job_id,
            "status": "completed",
            "progress": {"current_page": 1, "total_pages": 1, "percentage": 100}
        }
        
        return jsonify({
            "job_id": job_id,
            "status": "completed",
            "message": "Upload successful (conversion disabled for testing)"
        }), 202
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/jobs/<job_id>', methods=['GET'])
def status(job_id):
    if job_id in jobs:
        return jsonify(jobs[job_id]), 200
    return jsonify({"error": "Not found"}), 404

@app.route('/api/download/<job_id>', methods=['GET'])
def download(job_id):
    return jsonify({"error": "Conversion disabled in test mode"}), 400

if __name__ == '__main__':
    print("\n" + "="*60)
    print("  Simple Upload Test Server")
    print("  Conversion is DISABLED - testing uploads only")
    print("="*60 + "\n")
    app.run(host='0.0.0.0', port=5000, threaded=True)
