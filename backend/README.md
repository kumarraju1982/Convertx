# PDF to Word Converter - Backend

Flask REST API backend for converting scanned PDF files to editable Word documents using OCR.

## Features

- PDF to Word conversion using Tesseract OCR or Surya OCR
- **Surya OCR**: High-accuracy OCR for complex documents (tables, symbols, multi-column layouts)
- **Tesseract OCR**: Fast OCR for simple documents
- Asynchronous job processing with Celery and Redis
- REST API with file upload, status tracking, and download endpoints
- Automatic file cleanup after 24 hours
- Layout detection (paragraphs, headings, tables, lists)
- Multi-page document support

## Requirements

- Python 3.9+
- Redis server
- Tesseract OCR (for fast mode)
- PyTorch (for Surya OCR high-accuracy mode)

## Installation

### 1. Install Python Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Install Tesseract OCR (Optional - for fast mode)

**Windows:**
- Download installer from: https://github.com/UB-Mannheim/tesseract/wiki
- Install to: `C:\Program Files\Tesseract-OCR`
- Add to PATH or configure in `app/config.py`

**Linux:**
```bash
sudo apt-get install tesseract-ocr
```

**macOS:**
```bash
brew install tesseract
```

### 2b. Install PyTorch for Surya OCR (Recommended - for high accuracy)

Surya OCR provides significantly better accuracy for complex documents.

**CPU Version (no GPU):**
```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

**GPU Version (NVIDIA CUDA):**
```bash
pip install torch --index-url https://download.pytorch.org/whl/cu118
```

**Note:** Model weights (~500MB) will download automatically on first use.

### 3. Install and Start Redis

**Windows:**
- See `../install-redis-windows.md`

**Linux:**
```bash
sudo apt-get install redis-server
sudo systemctl start redis
```

**macOS:**
```bash
brew install redis
brew services start redis
```

## Configuration

Environment variables (optional):
```bash
# Redis Configuration
export REDIS_HOST=localhost
export REDIS_PORT=6379

# File Storage
export UPLOAD_FOLDER=../uploads

# OCR Engine Selection
export OCR_ENGINE=surya  # Options: 'tesseract' (fast) or 'surya' (accurate, default: tesseract)

# Tesseract Configuration (if using Tesseract)
export TESSERACT_CMD="C:\Program Files\Tesseract-OCR\tesseract.exe"  # Windows only
```

### OCR Engine Comparison

| Feature | Tesseract | Surya |
|---------|-----------|-------|
| Speed | Fast | Slower (2-3x) |
| Accuracy | Good | Excellent |
| Complex Documents | Fair | Excellent |
| Tables/Symbols | Fair | Excellent |
| Multi-column | Fair | Excellent |
| Languages | 100+ | 90+ |
| Installation | Small | Large (~500MB models) |

**Recommendation:** Use Surya for production quality, Tesseract for quick testing.

## Running the Application

### Development Mode

1. Start Redis (if not running):
```bash
redis-server
```

2. Start Celery worker:
```bash
celery -A app.celery_app worker --loglevel=info
```

3. Start Celery Beat (for periodic cleanup):
```bash
celery -A app.celery_app beat --loglevel=info
```

4. Start Flask API:
```bash
python -m app.api
```

The API will be available at `http://localhost:5000`

### Production Mode

Use Gunicorn for the Flask app:
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app.api:app
```

## API Endpoints

### POST /api/upload
Upload a PDF file for conversion.

**Request:**
- Content-Type: multipart/form-data
- Body: file (PDF, max 50MB)

**Response:**
```json
{
  "job_id": "uuid",
  "status": "pending",
  "message": "File uploaded successfully"
}
```

### GET /api/jobs/{job_id}
Get conversion job status.

**Response:**
```json
{
  "job_id": "uuid",
  "status": "processing",
  "progress": {
    "current_page": 2,
    "total_pages": 5,
    "percentage": 40
  },
  "created_at": "2024-01-01T12:00:00Z"
}
```

### GET /api/download/{job_id}
Download converted Word document.

**Response:** Binary file stream (.docx)

### GET /api/health
Health check endpoint.

## Testing

Run tests:
```bash
pytest backend/tests/ -v
```

Run with coverage:
```bash
pytest backend/tests/ --cov=app --cov-report=html
```

## Project Structure

```
backend/
├── app/
│   ├── api.py              # Flask REST API
│   ├── celery_app.py       # Celery configuration
│   ├── config.py           # Configuration
│   ├── document_parser.py  # PDF extraction
│   ├── file_manager.py     # File storage
│   ├── job_manager.py      # Job state management
│   ├── layout_analyzer.py  # Layout detection
│   ├── models.py           # Data models
│   ├── ocr_engine.py       # OCR processing
│   ├── pdf_converter.py    # Main orchestrator
│   ├── redis_client.py     # Redis connection
│   ├── tasks.py            # Celery tasks
│   └── word_generator.py   # Word document creation
├── tests/                  # Unit tests
└── requirements.txt        # Python dependencies
```

## Troubleshooting

### Tesseract Issues

**Tesseract not found:**
- Ensure Tesseract is installed and in PATH
- Or set `TESSERACT_CMD` environment variable
- Or switch to Surya OCR: `export OCR_ENGINE=surya`

### Surya OCR Issues

**Surya models not downloading:**
- Ensure you have internet connection on first run
- Models (~500MB) download to `~/.cache/huggingface/`
- Check disk space

**Surya running slow:**
- Surya is slower than Tesseract (expected)
- For faster processing, use GPU version of PyTorch
- Or switch to Tesseract for simple documents: `export OCR_ENGINE=tesseract`

**Out of memory errors:**
- Surya requires more RAM than Tesseract
- Reduce image size or use Tesseract for large documents
- Close other applications to free memory

**PyTorch/CUDA errors:**
- Ensure PyTorch is installed: `pip install torch`
- For CPU-only: `pip install torch --index-url https://download.pytorch.org/whl/cpu`
- For GPU: Ensure CUDA drivers are installed

### General Issues

**Redis connection error:**
- Ensure Redis server is running
- Check Redis host/port configuration

**File upload fails:**
- Check file size (max 50MB)
- Ensure file is a valid PDF
- Check disk space in upload folder
