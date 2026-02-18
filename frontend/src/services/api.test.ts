/**
 * Unit tests for API client service.
 * 
 * Tests cover upload, status polling, download, and error handling with mocked axios.
 */

import axios, { AxiosError } from 'axios';
import { JobResponse, JobStatusResponse, ApiError } from '../types/api';

// Mock axios before importing the API client
jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

// Set up mock axios instance before module import
const mockAxiosInstance = {
  post: jest.fn(),
  get: jest.fn(),
  interceptors: {
    response: {
      use: jest.fn(),
    },
  },
};

mockedAxios.create.mockReturnValue(mockAxiosInstance as any);

// Now import the API client after mocking
import ConversionAPI, { api } from './api';

describe('ConversionAPI', () => {
  let apiClient: ConversionAPI;

  beforeEach(() => {
    // Reset mocks
    jest.clearAllMocks();

    // Reset mock implementations
    mockAxiosInstance.post.mockReset();
    mockAxiosInstance.get.mockReset();

    // Create new API client instance
    apiClient = new ConversionAPI('/api');
  });

  describe('constructor', () => {
    it('should create axios instance with correct base URL', () => {
      expect(mockedAxios.create).toHaveBeenCalledWith({
        baseURL: '/api',
        headers: {
          'Content-Type': 'application/json',
        },
      });
    });

    it('should use default base URL when not provided', () => {
      const createSpy = jest.spyOn(mockedAxios, 'create');
      new ConversionAPI();

      expect(createSpy).toHaveBeenCalledWith({
        baseURL: '/api',
        headers: {
          'Content-Type': 'application/json',
        },
      });
    });

    it('should set up error interceptor', () => {
      expect(mockAxiosInstance.interceptors.response.use).toHaveBeenCalled();
    });
  });

  describe('uploadFile', () => {
    it('should upload file successfully', async () => {
      const mockFile = new File(['test content'], 'test.pdf', { type: 'application/pdf' });
      const mockResponse: JobResponse = {
        job_id: 'test-job-123',
        status: 'pending',
        message: 'File uploaded successfully',
      };

      mockAxiosInstance.post.mockResolvedValue({ data: mockResponse });

      const result = await apiClient.uploadFile(mockFile);

      expect(mockAxiosInstance.post).toHaveBeenCalledWith(
        '/upload',
        expect.any(FormData),
        expect.objectContaining({
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        })
      );
      expect(result).toEqual(mockResponse);
    });

    it('should include file in FormData', async () => {
      const mockFile = new File(['test content'], 'test.pdf', { type: 'application/pdf' });
      const mockResponse: JobResponse = {
        job_id: 'test-job-123',
        status: 'pending',
        message: 'File uploaded successfully',
      };

      mockAxiosInstance.post.mockResolvedValue({ data: mockResponse });

      await apiClient.uploadFile(mockFile);

      const callArgs = mockAxiosInstance.post.mock.calls[0];
      const formData = callArgs[1] as FormData;
      
      expect(formData).toBeInstanceOf(FormData);
      expect(formData.get('file')).toBe(mockFile);
    });

    it('should call onUploadProgress callback with progress percentage', async () => {
      const mockFile = new File(['test content'], 'test.pdf', { type: 'application/pdf' });
      const mockResponse: JobResponse = {
        job_id: 'test-job-123',
        status: 'pending',
        message: 'File uploaded successfully',
      };
      const onUploadProgress = jest.fn();

      mockAxiosInstance.post.mockImplementation((url, data, config) => {
        // Simulate upload progress
        if (config?.onUploadProgress) {
          config.onUploadProgress({ loaded: 50, total: 100 });
          config.onUploadProgress({ loaded: 100, total: 100 });
        }
        return Promise.resolve({ data: mockResponse });
      });

      await apiClient.uploadFile(mockFile, onUploadProgress);

      expect(onUploadProgress).toHaveBeenCalledWith(50);
      expect(onUploadProgress).toHaveBeenCalledWith(100);
    });

    it('should not call onUploadProgress when total is undefined', async () => {
      const mockFile = new File(['test content'], 'test.pdf', { type: 'application/pdf' });
      const mockResponse: JobResponse = {
        job_id: 'test-job-123',
        status: 'pending',
        message: 'File uploaded successfully',
      };
      const onUploadProgress = jest.fn();

      mockAxiosInstance.post.mockImplementation((url, data, config) => {
        if (config?.onUploadProgress) {
          config.onUploadProgress({ loaded: 50, total: undefined });
        }
        return Promise.resolve({ data: mockResponse });
      });

      await apiClient.uploadFile(mockFile, onUploadProgress);

      expect(onUploadProgress).not.toHaveBeenCalled();
    });

    it('should handle upload errors', async () => {
      const mockFile = new File(['test content'], 'test.pdf', { type: 'application/pdf' });
      const mockError = new Error('Upload failed');

      mockAxiosInstance.post.mockRejectedValue(mockError);

      await expect(apiClient.uploadFile(mockFile)).rejects.toThrow('Upload failed');
    });
  });

  describe('getJobStatus', () => {
    it('should retrieve job status successfully', async () => {
      const mockJobId = 'test-job-123';
      const mockResponse: JobStatusResponse = {
        job_id: mockJobId,
        status: 'processing',
        progress: {
          current_page: 2,
          total_pages: 5,
          percentage: 40,
        },
        created_at: '2024-01-01T00:00:00Z',
      };

      mockAxiosInstance.get.mockResolvedValue({ data: mockResponse });

      const result = await apiClient.getJobStatus(mockJobId);

      expect(mockAxiosInstance.get).toHaveBeenCalledWith(`/jobs/${mockJobId}`);
      expect(result).toEqual(mockResponse);
    });

    it('should handle completed job status', async () => {
      const mockJobId = 'test-job-123';
      const mockResponse: JobStatusResponse = {
        job_id: mockJobId,
        status: 'completed',
        progress: {
          current_page: 5,
          total_pages: 5,
          percentage: 100,
        },
        created_at: '2024-01-01T00:00:00Z',
        completed_at: '2024-01-01T00:05:00Z',
      };

      mockAxiosInstance.get.mockResolvedValue({ data: mockResponse });

      const result = await apiClient.getJobStatus(mockJobId);

      expect(result.status).toBe('completed');
      expect(result.completed_at).toBeDefined();
    });

    it('should handle failed job status with error message', async () => {
      const mockJobId = 'test-job-123';
      const mockResponse: JobStatusResponse = {
        job_id: mockJobId,
        status: 'failed',
        progress: {
          current_page: 2,
          total_pages: 5,
          percentage: 40,
        },
        error: 'OCR processing failed',
        created_at: '2024-01-01T00:00:00Z',
      };

      mockAxiosInstance.get.mockResolvedValue({ data: mockResponse });

      const result = await apiClient.getJobStatus(mockJobId);

      expect(result.status).toBe('failed');
      expect(result.error).toBe('OCR processing failed');
    });

    it('should handle status retrieval errors', async () => {
      const mockJobId = 'test-job-123';
      const mockError = new Error('Job not found');

      mockAxiosInstance.get.mockRejectedValue(mockError);

      await expect(apiClient.getJobStatus(mockJobId)).rejects.toThrow('Job not found');
    });
  });

  describe('downloadFile', () => {
    it('should download file successfully', async () => {
      const mockJobId = 'test-job-123';
      const mockBlob = new Blob(['test content'], { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' });

      mockAxiosInstance.get.mockResolvedValue({ data: mockBlob });

      const result = await apiClient.downloadFile(mockJobId);

      expect(mockAxiosInstance.get).toHaveBeenCalledWith(`/download/${mockJobId}`, {
        responseType: 'blob',
      });
      expect(result).toBe(mockBlob);
    });

    it('should handle download errors', async () => {
      const mockJobId = 'test-job-123';
      const mockError = new Error('File not found');

      mockAxiosInstance.get.mockRejectedValue(mockError);

      await expect(apiClient.downloadFile(mockJobId)).rejects.toThrow('File not found');
    });
  });

  describe('error interceptor', () => {
    let errorHandler: (error: any) => Promise<never>;

    beforeEach(() => {
      // Extract the error handler from the interceptor setup
      const interceptorCall = mockAxiosInstance.interceptors.response.use.mock.calls[0];
      errorHandler = interceptorCall[1];
    });

    it('should handle server error responses', () => {
      const mockError: Partial<AxiosError<ApiError>> = {
        response: {
          data: {
            error: 'ValidationError',
            message: 'Invalid file type',
          },
          status: 400,
          statusText: 'Bad Request',
          headers: {},
          config: {} as any,
        },
        isAxiosError: true,
      };

      expect(() => errorHandler(mockError)).toThrow('Invalid file type');
    });

    it('should handle server error without message', () => {
      const mockError: Partial<AxiosError<ApiError>> = {
        response: {
          data: {
            error: 'UnknownError',
            message: '',
          },
          status: 500,
          statusText: 'Internal Server Error',
          headers: {},
          config: {} as any,
        },
        isAxiosError: true,
      };

      expect(() => errorHandler(mockError)).toThrow('An error occurred');
    });

    it('should handle network errors (no response)', () => {
      const mockError: Partial<AxiosError> = {
        request: {},
        isAxiosError: true,
      };

      expect(() => errorHandler(mockError)).toThrow('No response from server. Please check your connection.');
    });

    it('should handle request setup errors', () => {
      const mockError: Partial<AxiosError> = {
        message: 'Request setup failed',
        isAxiosError: true,
      };

      expect(() => errorHandler(mockError)).toThrow('Failed to make request');
    });
  });

  describe('singleton instance', () => {
    it('should export a singleton instance', () => {
      expect(api).toBeInstanceOf(ConversionAPI);
    });
  });
});
