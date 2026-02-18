# Design Document: PDF to Word Converter

## Overview

The PDF to Word Converter is a web-based document processing application that transforms scanned PDF files into editable Microsoft Word documents. The system uses a three-tier architecture with a React frontend, Flask REST API backend, and asynchronous job processing pipeline.

The application leverages established libraries for core functionality:
- **Frontend**: React with TypeScript, Tailwind CSS for styling, Axios for API calls
- **Backend API**: Flask with Flask-CORS, Flask-RESTful for API endpoints
- **Job Queue**: Celery with Redis as message broker for async processing
- **PDF Processing**: PyMuPDF (fitz) or pdf2image for extracting page images
- **OCR Engine**: Tesseract OCR via pytesseract for text recognition
- **Word Generation**: python-docx for creating .docx files
- **Image Processing**: Pillow (PIL) for image preprocessing
- **File Storage**: Local filesystem with automatic cleanup

## Architecture

The system follows a three-tier architecture with clear separation between presentation, API, and processing layers:

```
[Browser] ←→ [React Frontend] ←→ [Flask API Server] ←→ [Celery Job Queue] → [Conversion Pipeline]
                                          ↓
                                   [File Storage]
```

### High-Level Flow

1. **Upload**: User uploads PDF via web interface → API stores file and creates job
2. **Queue**: API adds conversion job to Celery queue → returns job ID to frontend
3. **Process**: Celery worker picks up job → runs conversion pipeline → stores output
4. **Poll**: Frontend polls job status → displays progress → shows download when complete
5. **Download**: User downloads converted file → API serves file → cleanup after 24h

### Component Layers

**Presentation Layer (React Frontend)**:
- File upload UI with drag-and-drop
- Real-time progress display
- File download interface
- Responsive design for mobile/desktop

**API Layer (Flask Server)**:
- RESTful endpoints for upload, status, download
- File validation and storage
- Job creation and status tracking
- CORS handling for browser security

**Processing Layer (Celery Workers)**:
- Asynchronous job execution
- Conversion pipeline orchestration
- Progress updates during processing
- Error handling and retry logic

**Core Pipeline** (unchanged from original design):
```
[PDF File] → [Document Parser] → [OCR Engine] → [Layout Analyzer] → [Word Generator] → [.docx File]
```

## Components and Interfaces

### Web Layer Components

### 1. React Frontend

**Responsibility**: Provide user interface for file upload, progress tracking, and download.

**Key Components**:
```typescript
// Main upload component
interface UploadZoneProps {
  onFileSelected: (file: File) => void;
}

// Progress display component
interface ProgressDisplayProps {
  jobId: string;
  onComplete: (downloadUrl: string) => void;
}

// API client
interface ConversionAPI {
  uploadFile(file: File): Promise<JobResponse>;
  getJobStatus(jobId: string): Promise<JobStatus>;
  downloadFile(jobId: string): Promise<Blob>;
}
```

**JobResponse Structure**:
```typescript
{
  job_id: string;
  status: "pending" | "processing" | "completed" | "failed";
  message: string;
}
```

**JobStatus Structure**:
```typescript
{
  job_id: string;
  status: "pending" | "processing" | "completed" | "failed";
  progress: {
    current_page: number;
    total_pages: number;
    percentage: number;
  };
  error?: string;
  created_at: string;
  completed_at?: string;
}
```

### 2. Flask API Server

**Responsibility**: Handle HTTP requests, manage file storage, coordinate job processing.

**API Endpoints**:
```python
# File upload endpoint
POST /api/upload
Content-Type: multipart/form-data
Body: { file: <PDF file> }
Response: JobResponse

# Job status endpoint
GET /api/jobs/{job_id}
Response: JobStatus

# File download endpoint
GET /api/download/{job_id}
Response: Binary file stream (application/vnd.openxmlformats-officedocument.wordprocessingml.document)
```

**Flask Application Structure**:
```python
class ConversionAPI:
    def upload_file(file: FileStorage) -> JobResponse
    def get_job_status(job_id: str) -> JobStatus
    def download_file(job_id: str) -> Response
    def validate_file(file: FileStorage) -> ValidationResult
```

**ValidationResult Structure**:
```python
{
    "valid": bool,
    "error": str | None,
    "file_size": int,
    "file_type": str
}
```

### 3. Celery Job Queue

**Responsibility**: Manage asynchronous conversion jobs, track progress, handle failures.

**Task Interface**:
```python
@celery.task(bind=True)
def convert_pdf_task(self, job_id: str, input_path: str, output_path: str) -> TaskResult
```

**TaskResult Structure**:
```python
{
    "success": bool,
    "job_id": str,
    "output_path": str | None,
    "error": str | None,
    "pages_processed": int,
    "pages_failed": List[int]
}
```

**Job State Management**:
```python
class JobManager:
    def create_job(file_path: str) -> str  # Returns job_id
    def update_progress(job_id: str, current: int, total: int) -> None
    def mark_completed(job_id: str, output_path: str) -> None
    def mark_failed(job_id: str, error: str) -> None
    def get_status(job_id: str) -> JobStatus
```

### 4. File Manager

**Responsibility**: Handle file storage, retrieval, and cleanup.

**Interface**:
```python
class FileManager:
    def store_upload(file: FileStorage, job_id: str) -> str  # Returns file path
    def store_output(file_path: str, job_id: str) -> str
    def get_output_path(job_id: str) -> str | None
    def cleanup_old_files(max_age_hours: int = 24) -> int  # Returns count deleted
    def delete_job_files(job_id: str) -> None
```

**File Storage Structure**:
```
uploads/
  {job_id}/
    input.pdf
    output.docx
```

### Core Pipeline Components

### 5. PDF Converter (Main Orchestrator)

### 5. PDF Converter (Main Orchestrator)

**Responsibility**: Coordinates the conversion pipeline and manages the overall process.

**Interface**:
```python
class PDFConverter:
    def convert(pdf_path: str, output_path: str = None, progress_callback: Callable = None) -> ConversionResult
    def validate_pdf(pdf_path: str) -> ValidationResult
```

**ConversionResult Structure**:
```python
{
    "success": bool,
    "output_path": str,
    "pages_processed": int,
    "pages_failed": List[int],
    "errors": List[str]
}
```

### 6. Document Parser

**Responsibility**: Extract pages from PDF as images suitable for OCR.

**Interface**:
```python
class DocumentParser:
    def extract_pages(pdf_path: str) -> List[PageImage]
    def get_page_count(pdf_path: str) -> int
```

**PageImage Structure**:
```python
{
    "page_number": int,
    "image": PIL.Image,
    "width": int,
    "height": int,
    "dpi": int
}
```

### 7. OCR Engine

**Responsibility**: Extract text content and positioning information from images.

**Interface**:
```python
class OCREngine:
    def extract_text(image: PIL.Image) -> OCRResult
    def preprocess_image(image: PIL.Image) -> PIL.Image
```

**OCRResult Structure**:
```python
{
    "text": str,
    "words": List[WordBox],
    "confidence": float
}
```

**WordBox Structure**:
```python
{
    "text": str,
    "x": int,
    "y": int,
    "width": int,
    "height": int,
    "confidence": float
}
```

### 8. Layout Analyzer

**Responsibility**: Detect document structure from positioned text.

**Interface**:
```python
class LayoutAnalyzer:
    def analyze(ocr_result: OCRResult) -> DocumentStructure
```

**DocumentStructure**:
```python
{
    "elements": List[StructureElement]
}
```

**StructureElement** (discriminated union):
```python
{
    "type": "paragraph" | "heading" | "list" | "table",
    "content": str,
    "level": int (for headings),
    "style": dict
}
```

### 9. Word Generator

**Responsibility**: Create formatted Word documents from structured content.

**Interface**:
```python
class WordGenerator:
    def create_document(structures: List[DocumentStructure]) -> Document
    def save(document: Document, output_path: str) -> bool
```

## Data Models

### Web Request Flow

The web application follows this data flow:

```
User Upload → API Validation → Job Creation → Queue Processing → Status Polling → File Download
```

**Upload Flow**:
```
File (Browser) → FormData → POST /api/upload → FileStorage → store_upload() → Job Creation → JobResponse
```

**Status Flow**:
```
Timer (Browser) → GET /api/jobs/{id} → JobManager.get_status() → JobStatus → UI Update
```

**Download Flow**:
```
Click (Browser) → GET /api/download/{id} → FileManager.get_output_path() → send_file() → Blob
```

### Job Lifecycle

Jobs transition through states:

```
pending → processing → completed
                    ↘ failed
```

**State Transitions**:
- `pending`: Job created, waiting for worker
- `processing`: Worker picked up job, conversion in progress
- `completed`: Conversion successful, file ready for download
- `failed`: Conversion failed, error message available

### Page Processing Pipeline

Each page flows through the pipeline as a series of transformations (unchanged):

```
PDF Page → PageImage → OCRResult → DocumentStructure → Word Paragraph/Table
```

### Error Tracking

Errors are accumulated during processing:

```python
{
    "page_number": int,
    "stage": "parsing" | "ocr" | "layout" | "generation",
    "error_type": str,
    "message": str
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property 1: PDF Validation Correctness
*For any* file path, the PDF validator should correctly identify valid PDF files and reject invalid or non-existent files with appropriate error messages.
**Validates: Requirements 1.1, 1.2**

### Property 2: Page Extraction Order Preservation
*For any* valid PDF file, extracting pages should produce images in the same order as they appear in the original PDF, with all pages included.
**Validates: Requirements 1.3, 1.4**

### Property 3: OCR Text Extraction Completeness
*For any* page image containing text, the OCR engine should extract all visible text content with confidence scores.
**Validates: Requirements 2.1, 2.5**

### Property 4: Reading Order Preservation
*For any* page image with positioned text, the OCR engine should extract text in the correct reading order (left-to-right, top-to-bottom).
**Validates: Requirements 2.2**

### Property 5: Error Resilience in Multi-Page Processing
*For any* multi-page PDF where some pages fail OCR processing, the converter should continue processing remaining pages, log errors, and report which pages failed.
**Validates: Requirements 2.3, 5.3**

### Property 6: Layout Structure Detection
*For any* OCR result with structured text, the layout analyzer should correctly identify document elements (paragraphs, headings, tables, lists, columns).
**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**

### Property 7: Valid Word Document Generation
*For any* document structure, the Word generator should create a valid .docx file that can be opened by Microsoft Word or compatible applications.
**Validates: Requirements 4.1**

### Property 8: Structure and Formatting Preservation
*For any* document structure with formatting (headings, paragraphs, lists, tables), the generated Word document should contain corresponding formatted elements.
**Validates: Requirements 4.2, 4.3**

### Property 9: Output File Path Handling
*For any* valid output path, the Word generator should save the document to that location; for invalid paths, it should return a descriptive error before processing.
**Validates: Requirements 4.4, 4.5, 6.4**

### Property 10: Multi-Page Document Consolidation
*For any* multi-page PDF, the converter should process all pages sequentially and combine them into a single Word document with page breaks preserved.
**Validates: Requirements 5.1, 5.2, 5.4**

### Property 11: Specific Error Messages
*For any* file I/O error or unsupported format, the system should return specific error messages that clearly indicate the failure type.
**Validates: Requirements 6.1, 6.2**

### Property 12: Image Resolution Support
*For any* image with resolution between 150-600 DPI, the OCR engine should successfully process it.
**Validates: Requirements 7.1**

### Property 13: Image Preprocessing Application
*For any* low-quality image, the OCR engine should apply preprocessing before text extraction.
**Validates: Requirements 7.2**

### Property 14: Special Character Recognition
*For any* text containing common symbols and punctuation, the OCR engine should recognize these characters.
**Validates: Requirements 7.3**

### Property 15: English Language Support
*For any* English text in an image, the OCR engine should successfully recognize it.
**Validates: Requirements 7.4**

### Property 16: Default Output Path Generation
*For any* input PDF without a specified output path, the converter should create the Word file in the same directory as the input, using the input filename with .docx extension.
**Validates: Requirements 8.1, 8.4**

### Property 17: Output Directory Validation
*For any* specified output path, the converter should validate that the directory exists before processing.
**Validates: Requirements 8.2**

### Property 18: File Conflict Handling
*For any* output path where a file already exists, the converter should handle the conflict according to configuration (overwrite or generate unique filename).
**Validates: Requirements 8.3**

### Property 19: File Upload Validation
*For any* uploaded file, the API server should correctly validate file type and size, accepting valid PDFs up to 50MB and rejecting invalid files with descriptive error messages.
**Validates: Requirements 9.3, 9.4, 9.5**

### Property 20: Unique Job Identifier Generation
*For any* set of file uploads, all generated job identifiers should be unique.
**Validates: Requirements 9.6**

### Property 21: Job Queue Addition
*For any* conversion job created, the job should be added to the processing queue.
**Validates: Requirements 10.1**

### Property 22: Job State Transitions
*For any* job, the status should correctly transition through states: pending → processing → completed/failed, with appropriate error details when failed.
**Validates: Requirements 10.2, 10.3, 10.4, 10.5**

### Property 23: Progress Information Storage
*For any* job being processed, progress information (current page, total pages) should be stored and retrievable.
**Validates: Requirements 10.6**

### Property 24: Job Status API Response
*For any* job ID, requesting status through the API should return current progress information.
**Validates: Requirements 11.1**

### Property 25: UI Progress Display
*For any* job with progress data, the web interface should display progress bar, current page, and total page count; when completed, should display download button.
**Validates: Requirements 11.2, 11.3, 11.5**

### Property 26: Output File Storage
*For any* completed conversion, the output file should be stored and retrievable using the job identifier.
**Validates: Requirements 12.1, 12.2**

### Property 27: Download Filename Preservation
*For any* file download, the filename should be the original PDF filename with .docx extension.
**Validates: Requirements 12.3**

### Property 28: File Cleanup After Expiration
*For any* file stored for more than 24 hours, the file manager should delete it during cleanup operations.
**Validates: Requirements 12.4**

### Property 29: Non-existent File Error Handling
*For any* request for a deleted or non-existent job file, the API should return a 404 error.
**Validates: Requirements 12.5**

### Property 30: API Error Status Codes
*For any* invalid API request, the server should return appropriate HTTP status codes (400 for bad requests, 404 for not found, 500 for server errors).
**Validates: Requirements 13.4**

### Property 31: API Response Consistency
*For any* successful API call, the response should follow a consistent JSON structure with predictable fields.
**Validates: Requirements 13.5**

### Property 32: Responsive Layout Adaptation
*For any* viewport size change, the web interface should adapt the layout responsively.
**Validates: Requirements 14.3**

### Property 33: Touch Gesture Handling
*For any* touch gesture (tap, swipe), the web interface should respond appropriately.
**Validates: Requirements 14.4**

### Property 34: Accessibility Compliance
*For any* interactive element in the web interface, it should meet WCAG 2.1 Level AA standards including keyboard navigation, ARIA labels, and sufficient color contrast.
**Validates: Requirements 15.5**

## Error Handling

The system implements a layered error handling strategy across web and processing layers:

### Web Layer Error Handling

**API Request Validation**:
- Validate file uploads (type, size, format) before accepting
- Return 400 Bad Request for invalid uploads with descriptive messages
- Return 404 Not Found for non-existent job IDs
- Return 500 Internal Server Error for unexpected failures
- Use consistent JSON error response format:
  ```json
  {
    "error": "Error type",
    "message": "Descriptive error message",
    "details": {}
  }
  ```

**Job Queue Error Handling**:
- Catch exceptions during job processing
- Update job status to "failed" with error details
- Implement retry logic for transient failures (network, temporary file issues)
- Log all errors with job context for debugging
- Clean up partial files on failure

**CORS and Security**:
- Handle CORS preflight requests properly
- Validate file types on server side (don't trust client)
- Implement file size limits to prevent DoS
- Sanitize filenames to prevent path traversal attacks

### Input Validation Layer
- Validate file existence and format before processing
- Validate output paths before starting conversion
- Return early with clear error messages for invalid inputs

### Processing Layer
- Catch exceptions at each pipeline stage
- Log errors with context (page number, stage, error type)
- Continue processing when possible (e.g., skip failed pages)
- Accumulate errors for final reporting

### Resource Management
- Use context managers for file handles
- Clean up temporary image files after processing
- Release memory for large images after OCR
- Implement automatic cleanup of old job files

### Error Types

```python
class ConversionError(Exception):
    """Base exception for conversion errors"""
    pass

class PDFValidationError(ConversionError):
    """Invalid or corrupted PDF file"""
    pass

class OCRProcessingError(ConversionError):
    """OCR processing failed"""
    pass

class WordGenerationError(ConversionError):
    """Word document generation failed"""
    pass

class FileIOError(ConversionError):
    """File input/output operation failed"""
    pass

class JobNotFoundError(ConversionError):
    """Job ID does not exist"""
    pass

class FileUploadError(ConversionError):
    """File upload validation failed"""
    pass
```

## Testing Strategy

The testing strategy employs both unit tests and property-based tests to ensure comprehensive coverage across frontend, API, and processing layers.

### Frontend Testing Approach

**Unit Tests (Jest + React Testing Library)**:
- Component rendering with different props
- User interaction handling (file selection, drag-and-drop)
- API call mocking and response handling
- Progress display updates
- Error message display

**Integration Tests**:
- File upload flow from UI to API
- Status polling and UI updates
- Download button functionality
- Responsive layout at different viewports

**Accessibility Tests**:
- Keyboard navigation
- Screen reader compatibility
- ARIA labels and roles
- Color contrast ratios

### API Testing Approach

**Unit Tests (pytest)**:
- Endpoint routing and request handling
- File validation logic
- Job creation and status tracking
- Error response formatting
- CORS header handling

**Property-Based Tests**:
- File upload validation with various file types and sizes
- Job ID uniqueness across multiple uploads
- Status endpoint responses for all job states
- Error handling for invalid requests

**Integration Tests**:
- Full upload → process → download flow
- Concurrent job handling
- File cleanup operations
- Database/Redis interactions

### Backend Processing Testing Approach

Unit tests focus on:
- Specific examples of PDF processing (single page, multi-page, empty)
- Edge cases (empty PDFs, blank pages, unsupported formats)
- Error conditions (invalid paths, corrupted files, I/O failures)
- Integration between components (pipeline flow)

Each component should have unit tests that verify:
- Expected behavior with valid inputs
- Proper error handling with invalid inputs
- Edge case handling

### Property-Based Testing Approach

Property-based tests verify universal properties using PBT libraries:
- **Frontend**: fast-check for TypeScript/JavaScript
- **Backend**: Hypothesis for Python

**Configuration**:
- Minimum 100 iterations per property test
- Each test tagged with: **Feature: pdf-to-word-converter, Property {N}: {property_text}**

**Test Generators**:

*Frontend Generators*:
- Generate job status objects with various states
- Generate progress data with different page counts
- Generate file objects with various types and sizes
- Generate viewport dimensions for responsive testing

*Backend Generators*:
- Generate PDFs with varying page counts (0-10 pages)
- Generate images with different resolutions (150-600 DPI)
- Generate text with various layouts (paragraphs, headings, tables)
- Generate valid and invalid file paths
- Generate text with special characters and punctuation
- Generate job IDs and timestamps for cleanup testing

**Property Test Coverage**:
- Each correctness property (1-34) should have a corresponding property-based test
- Tests should generate random valid inputs and verify the property holds
- Tests should generate random invalid inputs and verify proper error handling

### Testing Balance

- Unit tests provide concrete examples and catch specific bugs
- Property tests provide comprehensive input coverage and verify general correctness
- Integration tests verify components work together correctly
- Together they ensure both specific cases work and universal properties hold

### Test Data

For testing, we'll need:
- Sample scanned PDFs (single page, multi-page, various layouts)
- Sample images with known text content
- Invalid/corrupted PDF files for error testing
- PDFs with tables, lists, headings for layout testing
- Mock API responses for frontend testing
- Test job data for queue testing

### End-to-End Testing

**Manual Testing Checklist**:
- Upload various PDF files through web UI
- Verify progress updates during conversion
- Download and verify converted Word documents
- Test on different browsers (Chrome, Firefox, Safari)
- Test on mobile devices (iOS, Android)
- Verify file cleanup after 24 hours

**Automated E2E Tests (Optional)**:
- Use Playwright or Cypress for browser automation
- Test complete user flows
- Test error scenarios
- Test concurrent users

## Implementation Notes

### Technology Stack

**Frontend**:
- **React 18+** with TypeScript for type safety
- **Tailwind CSS** for utility-first styling and responsive design
- **Axios** for HTTP requests with interceptors
- **React Dropzone** for drag-and-drop file upload
- **Lucide React** or **Heroicons** for icon library

**Backend API**:
- **Flask 3.0+** for lightweight REST API
- **Flask-CORS** for cross-origin resource sharing
- **Flask-RESTful** for API resource organization
- **Werkzeug** for secure file handling

**Job Queue**:
- **Celery 5.0+** for distributed task queue
- **Redis** as message broker and result backend
- **Flower** (optional) for monitoring Celery workers

**Core Processing** (unchanged):
- **PyMuPDF (fitz)**: Fast PDF processing, good image extraction
- **Tesseract OCR**: Industry-standard open-source OCR
- **python-docx**: Standard library for Word document generation
- **Pillow**: Comprehensive image processing

### Library Selection Rationale

**React + TypeScript**: Type safety prevents runtime errors, React's component model fits the UI well
**Tailwind CSS**: Rapid UI development, easy responsive design, professional look with minimal custom CSS
**Flask**: Lightweight, easy to set up REST APIs, good for Python integration
**Celery + Redis**: Industry-standard for async job processing, scalable, reliable
**PyMuPDF/Tesseract/python-docx**: Same rationale as original design - proven, widely used

### Performance Considerations

**Frontend**:
- Implement debouncing for status polling (every 1-2 seconds)
- Use React.memo for expensive components
- Lazy load components for faster initial load
- Compress uploaded files if possible before sending

**API**:
- Stream large file uploads/downloads to manage memory
- Implement request rate limiting to prevent abuse
- Use connection pooling for Redis
- Cache job status for frequently polled jobs

**Processing**:
- Large PDFs should be processed page-by-page to manage memory
- OCR is CPU-intensive; Celery workers can run on multiple machines
- Image preprocessing can improve OCR accuracy but adds processing time
- Temporary image files should be cleaned up promptly

**File Storage**:
- Implement automatic cleanup of files older than 24 hours
- Consider cloud storage (S3) for production deployments
- Use unique job IDs to prevent filename conflicts

### Deployment Considerations

**Development Setup**:
```
Frontend: npm run dev (port 3000)
Backend: flask run (port 5000)
Redis: redis-server (port 6379)
Celery: celery -A app.celery worker
```

**Production Setup**:
- Frontend: Build static files, serve with Nginx or CDN
- Backend: Use Gunicorn or uWSGI with multiple workers
- Redis: Configure persistence and memory limits
- Celery: Run multiple workers, configure concurrency
- Reverse proxy: Nginx for SSL, load balancing, static files

### Security Considerations

- Validate file types on server (don't trust client MIME types)
- Implement file size limits (50MB default)
- Sanitize filenames to prevent path traversal
- Use HTTPS in production
- Implement rate limiting on upload endpoint
- Set CORS to specific origins in production
- Clean up uploaded files after processing

### Future Enhancements

**Core Features**:
- Support for additional languages in OCR
- Parallel processing for multi-page documents
- Image quality assessment and automatic enhancement
- Support for embedded images in PDFs (not just text)
- Batch processing of multiple PDFs

**Web Features**:
- User accounts and conversion history
- WebSocket for real-time progress updates (instead of polling)
- Drag-and-drop multiple files
- Preview of converted document before download
- Email notification when conversion completes
- API authentication and rate limiting per user
- Cloud storage integration (Google Drive, Dropbox)
- Mobile app (React Native)
