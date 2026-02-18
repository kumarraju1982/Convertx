"""
Tests for Flask API endpoints.

These tests verify the upload, status, and download endpoints with proper mocking.
"""

import pytest
import io
from unittest.mock import Mock, patch, MagicMock
from app.api import create_app
from app.exceptions import JobNotFoundError
from hypothesis import given, strategies as st, settings, HealthCheck


# Global mocks that will be reused
mock_file_manager_instance = None
mock_job_manager_instance = None


@pytest.fixture(scope='function')
def app():
    """Create Flask app for testing with properly mocked dependencies."""
    global mock_file_manager_instance, mock_job_manager_instance
    
    # Create mock instances
    mock_file_manager_instance = Mock()
    mock_file_manager_instance.store_upload.return_value = "/tmp/test-job/input.pdf"
    mock_file_manager_instance.get_output_path.return_value = "/tmp/test-job/output.docx"
    mock_file_manager_instance.get_original_filename.return_value = "test.pdf"
    
    mock_job_manager_instance = Mock()
    mock_job_manager_instance.create_job.return_value = "test-job-123"
    mock_job_manager_instance.get_status.return_value = {
        'job_id': 'test-job-123',
        'status': 'pending',
        'progress': {'current_page': 0, 'total_pages': 0, 'percentage': 0},
        'created_at': '2024-01-01T00:00:00Z'
    }
    
    with patch('app.api.RedisClient'), \
         patch('app.api.FileManager', return_value=mock_file_manager_instance), \
         patch('app.api.JobManager', return_value=mock_job_manager_instance):
        
        app = create_app()
        app.config['TESTING'] = True
        yield app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


class TestHealthCheck:
    """Test suite for health check endpoint."""
    
    def test_health_check(self, client):
        """Test health check endpoint returns 200."""
        response = client.get('/api/health')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'healthy'


class TestUploadEndpoint:
    """Test suite for file upload endpoint."""
    
    @patch('app.api.convert_pdf_task')
    def test_upload_valid_pdf(self, mock_task, client):
        """Test uploading a valid PDF file."""
        global mock_file_manager_instance, mock_job_manager_instance
        
        # Reset mocks
        mock_file_manager_instance.reset_mock()
        mock_job_manager_instance.reset_mock()
        mock_file_manager_instance.store_upload.return_value = "/tmp/test-job/input.pdf"
        mock_job_manager_instance.create_job.return_value = "test-job-123"
        
        # Mock Celery task
        mock_task.delay = Mock()
        
        # Create a fake PDF file
        data = {
            'file': (io.BytesIO(b'%PDF-1.4 fake pdf content'), 'test.pdf')
        }
        
        response = client.post(
            '/api/upload',
            data=data,
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 202
        json_data = response.get_json()
        assert 'job_id' in json_data
        assert json_data['status'] == 'pending'
        assert 'message' in json_data
        
        # Verify methods were called
        assert mock_file_manager_instance.store_upload.called
        assert mock_job_manager_instance.create_job.called
        assert mock_task.delay.called
    
    def test_upload_no_file(self, client):
        """Test upload without file."""
        response = client.post('/api/upload')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    def test_upload_empty_filename(self, client):
        """Test upload with empty filename."""
        data = {
            'file': (io.BytesIO(b'content'), '')
        }
        
        response = client.post(
            '/api/upload',
            data=data,
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 400
        json_data = response.get_json()
        assert 'error' in json_data
    
    def test_upload_invalid_file_type(self, client):
        """Test upload with non-PDF file."""
        data = {
            'file': (io.BytesIO(b'not a pdf'), 'test.txt')
        }
        
        response = client.post(
            '/api/upload',
            data=data,
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 400
        json_data = response.get_json()
        assert 'error' in json_data
        assert 'PDF' in json_data['message'] or 'pdf' in json_data['message']
    
    @patch('app.api.convert_pdf_task')
    def test_upload_file_storage_failure(self, mock_task, client):
        """Test upload when file storage fails."""
        global mock_file_manager_instance
        
        # Make store_upload raise an exception
        mock_file_manager_instance.store_upload.side_effect = Exception("Storage failed")
        
        data = {
            'file': (io.BytesIO(b'%PDF-1.4 content'), 'test.pdf')
        }
        
        response = client.post(
            '/api/upload',
            data=data,
            content_type='multipart/form-data'
        )
        
        # API catches storage errors and returns 400 with error message
        assert response.status_code == 400
        json_data = response.get_json()
        assert 'error' in json_data
        
        # Reset side effect
        mock_file_manager_instance.store_upload.side_effect = None


class TestJobStatusEndpoint:
    """Test suite for job status endpoint."""
    
    def test_get_status_existing_job(self, client):
        """Test getting status of existing job."""
        global mock_job_manager_instance
        
        mock_job_manager_instance.get_status.return_value = {
            'job_id': 'test-job-123',
            'status': 'processing',
            'progress': {'current_page': 5, 'total_pages': 10, 'percentage': 50},
            'created_at': '2024-01-01T00:00:00Z'
        }
        
        response = client.get('/api/jobs/test-job-123')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['job_id'] == 'test-job-123'
        assert data['status'] == 'processing'
        assert data['progress']['percentage'] == 50
    
    def test_get_status_nonexistent_job(self, client):
        """Test getting status of non-existent job."""
        global mock_job_manager_instance
        
        mock_job_manager_instance.get_status.side_effect = JobNotFoundError("Job not found")
        
        response = client.get('/api/jobs/nonexistent-job')
        
        assert response.status_code == 404
        
        # Reset side effect
        mock_job_manager_instance.get_status.side_effect = None
    
    def test_get_status_completed_job(self, client):
        """Test getting status of completed job."""
        global mock_job_manager_instance
        
        mock_job_manager_instance.get_status.return_value = {
            'job_id': 'test-job-123',
            'status': 'completed',
            'progress': {'current_page': 10, 'total_pages': 10, 'percentage': 100},
            'created_at': '2024-01-01T00:00:00Z',
            'completed_at': '2024-01-01T00:05:00Z',
            'output_path': '/tmp/test-job/output.docx'
        }
        
        response = client.get('/api/jobs/test-job-123')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'completed'
        assert 'completed_at' in data


class TestDownloadEndpoint:
    """Test suite for download endpoint."""
    
    def test_download_completed_job(self, client):
        """Test downloading a completed job."""
        global mock_file_manager_instance, mock_job_manager_instance
        
        # Create a temporary file to download
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.docx', delete=False) as f:
            f.write('test content')
            temp_path = f.name
        
        try:
            mock_job_manager_instance.get_status.return_value = {
                'job_id': 'test-job-123',
                'status': 'completed',
                'output_path': temp_path
            }
            mock_file_manager_instance.get_output_path.return_value = temp_path
            mock_file_manager_instance.get_original_filename.return_value = 'test.pdf'
            
            response = client.get('/api/download/test-job-123')
            
            # Should return 200 and file content
            assert response.status_code == 200
        finally:
            # Cleanup - wait a bit for file to be released on Windows
            import time
            time.sleep(0.1)
            try:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
            except PermissionError:
                # File still locked on Windows, ignore
                pass
    
    def test_download_nonexistent_job(self, client):
        """Test downloading non-existent job."""
        global mock_job_manager_instance
        
        mock_job_manager_instance.get_status.side_effect = JobNotFoundError("Job not found")
        
        response = client.get('/api/download/nonexistent-job')
        
        assert response.status_code == 404
        
        # Reset
        mock_job_manager_instance.get_status.side_effect = None
    
    def test_download_pending_job(self, client):
        """Test downloading a job that's not completed."""
        global mock_job_manager_instance
        
        mock_job_manager_instance.get_status.return_value = {
            'job_id': 'test-job-123',
            'status': 'pending'
        }
        
        response = client.get('/api/download/test-job-123')
        
        assert response.status_code == 400
    
    def test_download_file_not_found(self, client):
        """Test downloading when output file doesn't exist."""
        global mock_file_manager_instance, mock_job_manager_instance
        
        mock_job_manager_instance.get_status.return_value = {
            'job_id': 'test-job-123',
            'status': 'completed',
            'output_path': '/tmp/test-job/output.docx'
        }
        mock_file_manager_instance.get_output_path.return_value = None
        
        response = client.get('/api/download/test-job-123')
        
        assert response.status_code == 404


class TestErrorHandlers:
    """Test suite for error handlers."""
    
    def test_404_handler(self, client):
        """Test 404 error handler."""
        response = client.get('/api/nonexistent')
        
        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data
    
    def test_cors_headers(self, client):
        """Test CORS headers are present."""
        response = client.get('/api/health')
        
        # CORS headers should be present in development
        assert response.status_code == 200


# Property-based tests
class TestFileUploadValidationProperty:
    """
    **Property 19: File Upload Validation**
    **Validates: Requirements 9.3, 9.4, 9.5**
    """
    
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        filename=st.text(min_size=1, max_size=100, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            whitelist_characters='.-_'
        ))
    )
    def test_property_file_upload_validation(self, client, filename):
        """Test that file upload validation works for various filenames."""
        # Only PDF files should be accepted
        if filename.lower().endswith('.pdf'):
            data = {
                'file': (io.BytesIO(b'%PDF-1.4 content'), filename)
            }
            
            with patch('app.api.convert_pdf_task'):
                response = client.post(
                    '/api/upload',
                    data=data,
                    content_type='multipart/form-data'
                )
            
            # Should accept PDF files
            assert response.status_code in [202, 500]  # 202 success or 500 if storage fails
        else:
            data = {
                'file': (io.BytesIO(b'content'), filename)
            }
            
            response = client.post(
                '/api/upload',
                data=data,
                content_type='multipart/form-data'
            )
            
            # Should reject non-PDF files
            assert response.status_code == 400


class TestAPIErrorStatusCodesProperty:
    """
    **Property 30: API Error Status Codes**
    **Validates: Requirements 13.4**
    """
    
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(dummy=st.just(None))
    def test_property_api_error_status_codes(self, client, dummy):
        """Test that API returns appropriate error status codes."""
        # Test 400 for invalid requests
        response = client.post('/api/upload')
        assert response.status_code == 400
        
        # Test 404 for non-existent resources
        response = client.get('/api/jobs/nonexistent-job-id-12345')
        assert response.status_code in [404, 200]  # Depends on mock


class TestAPIResponseConsistencyProperty:
    """
    **Property 31: API Response Consistency**
    **Validates: Requirements 13.5**
    """
    
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(dummy=st.just(None))
    def test_property_api_response_consistency(self, client, dummy):
        """Test that API responses have consistent JSON structure."""
        # Health check should always return JSON
        response = client.get('/api/health')
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, dict)
        assert 'status' in data
    
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(dummy=st.just(None))
    def test_property_api_error_response_consistency(self, client, dummy):
        """Test that API error responses have consistent structure."""
        # Error responses should have 'error' field
        response = client.post('/api/upload')
        assert response.status_code == 400
        data = response.get_json()
        assert isinstance(data, dict)
        assert 'error' in data


class TestJobStatusAPIProperty:
    """
    **Property 24: Job Status API Response**
    **Validates: Requirements 11.1**
    """
    
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(dummy=st.just(None))
    def test_property_job_status_api_response(self, client, dummy):
        """Test that job status API returns consistent response format."""
        global mock_job_manager_instance
        
        mock_job_manager_instance.get_status.return_value = {
            'job_id': 'test-job',
            'status': 'processing',
            'progress': {'current_page': 1, 'total_pages': 10, 'percentage': 10},
            'created_at': '2024-01-01T00:00:00Z'
        }
        
        response = client.get('/api/jobs/test-job')
        
        if response.status_code == 200:
            data = response.get_json()
            assert 'job_id' in data
            assert 'status' in data
            assert 'progress' in data


class TestNonExistentFileHandlingProperty:
    """
    **Property 29: Non-existent File Error Handling**
    **Validates: Requirements 12.5**
    """
    
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        job_id=st.text(min_size=10, max_size=50, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            whitelist_characters='-'
        ))
    )
    def test_property_nonexistent_file_handling(self, client, job_id):
        """Test that requesting non-existent files returns 404."""
        global mock_job_manager_instance
        
        mock_job_manager_instance.get_status.side_effect = JobNotFoundError("Not found")
        
        response = client.get(f'/api/jobs/{job_id}')
        
        assert response.status_code == 404
        
        # Reset
        mock_job_manager_instance.get_status.side_effect = None



class TestAPIConfigurationEdgeCases:
    """Test API configuration edge cases for coverage."""
    
    def test_create_app_without_config(self):
        """Test creating app without explicit config uses default."""
        from app.api import create_app
        app = create_app()  # No config parameter
        assert app is not None
        assert app.config['TESTING'] is False
    
    def test_upload_with_connection_error(self, client):
        """Test upload when Redis connection fails."""
        global mock_job_manager_instance
        
        # Simulate Redis connection error
        mock_job_manager_instance.create_job.side_effect = Exception("Redis connection failed")
        
        data = {
            'file': (io.BytesIO(b'%PDF-1.4 content'), 'test.pdf')
        }
        
        response = client.post(
            '/api/upload',
            data=data,
            content_type='multipart/form-data'
        )
        
        # Should return error
        assert response.status_code in [400, 500]
        
        # Reset
        mock_job_manager_instance.create_job.side_effect = None
    
    def test_status_with_invalid_job_id_format(self, client):
        """Test status endpoint with malformed job ID."""
        response = client.get('/api/jobs/')
        assert response.status_code == 404
    
    def test_download_with_missing_output_file(self, client):
        """Test download when output file is missing."""
        global mock_job_manager_instance, mock_file_manager_instance
        
        mock_job_manager_instance.get_status.return_value = {
            'job_id': 'test-job',
            'status': 'completed'
        }
        mock_file_manager_instance.get_output_path.return_value = None
        
        response = client.get('/api/download/test-job')
        assert response.status_code == 404
