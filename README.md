# PDF to Word Converter

A full-stack web application that converts scanned PDF files into editable Microsoft Word documents using OCR technology.

## Features

- Web-based file upload with drag-and-drop support
- Asynchronous conversion processing with real-time progress tracking
- OCR-powered text extraction from scanned PDFs
- Layout and formatting preservation (paragraphs, headings, tables, lists)
- Responsive design for mobile and desktop
- RESTful API for integration

## Architecture

- **Frontend**: React with TypeScript, Tailwind CSS, Vite
- **Backend API**: Flask with Flask-CORS and Flask-RESTful
- **Job Queue**: Celery with Redis
- **PDF Processing**: PyMuPDF (fitz)
- **OCR Engine**: Tesseract OCR
- **Word Generation**: python-docx

## Project Structure

```
.
├── frontend/          # React TypeScript frontend
│   ├── src/
│   ├── public/
│   └── package.json
├── backend/           # Flask Python backend
│   ├── app/
│   ├── tests/
│   └── requirements.txt
└── README.md
```

## Prerequisites

### Backend
- Python 3.9+
- Redis server
- Tesseract OCR installed on system

### Frontend
- Node.js 18+
- npm or yarn

## Setup Instructions

### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install Tesseract OCR:
- **Ubuntu/Debian**: `sudo apt-get install tesseract-ocr`
- **macOS**: `brew install tesseract`
- **Windows**: Download from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)

5. Start Redis server:
```bash
redis-server
```

6. Run Flask development server:
```bash
flask run
```

7. In a separate terminal, start Celery worker:
```bash
celery -A app.celery worker --loglevel=info
```

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start development server:
```bash
npm run dev
```

4. Open browser to http://localhost:3000

## Testing

### Backend Tests
```bash
cd backend
pytest
```

### Frontend Tests
```bash
cd frontend
npm test
```

## API Endpoints

- `POST /api/upload` - Upload PDF file for conversion (max 50MB)
- `GET /api/jobs/{job_id}` - Get conversion job status and progress
- `GET /api/download/{job_id}` - Download converted Word document
- `GET /api/health` - Health check endpoint

## Configuration

### Backend Environment Variables (Optional)

- `REDIS_HOST` - Redis server host (default: localhost)
- `REDIS_PORT` - Redis server port (default: 6379)
- `UPLOAD_FOLDER` - File storage location (default: ../uploads)
- `TESSERACT_CMD` - Tesseract executable path (Windows only)

### Frontend Configuration

API proxy is configured in `frontend/vite.config.ts` for development.

For production, update the API base URL in `frontend/src/services/api.ts`.

## Troubleshooting

**Tesseract not found:**
- Ensure Tesseract is installed and in PATH
- Windows: Set `TESSERACT_CMD` environment variable to Tesseract path

**Redis connection error:**
- Ensure Redis server is running: `redis-server`
- Check Redis host/port configuration

**File upload fails:**
- Check file size (max 50MB)
- Ensure file is a valid PDF
- Check disk space in upload folder

**Conversion fails:**
- Check Tesseract installation
- Verify PDF is not password-protected
- Check backend logs for detailed errors

## Development

- Backend runs on port 5000
- Frontend runs on port 3000
- Frontend proxies API requests to backend

## License

MIT
