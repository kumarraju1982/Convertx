/**
 * API client for PDF to Word conversion service.
 * 
 * This module provides methods for interacting with the Flask backend API.
 */

import axios, { AxiosInstance, AxiosError } from 'axios';
import { JobResponse, JobStatusResponse, ApiError } from '../types/api';

class ConversionAPI {
  private client: AxiosInstance;

  constructor(baseURL: string = import.meta.env.VITE_API_URL || '/api') {
    this.client = axios.create({
      baseURL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add error interceptor
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError<ApiError>) => {
        if (error.response) {
          // Server responded with error
          throw new Error(error.response.data.message || 'An error occurred');
        } else if (error.request) {
          // Request made but no response
          throw new Error('No response from server. Please check your connection.');
        } else {
          // Error setting up request
          throw new Error('Failed to make request');
        }
      }
    );
  }

  /**
   * Upload a PDF file for conversion.
   * 
   * @param file - PDF file to upload
   * @param onUploadProgress - Optional callback for upload progress (0-100)
   * @returns Promise with job response
   */
  async uploadFile(
    file: File,
    onUploadProgress?: (progress: number) => void
  ): Promise<JobResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await this.client.post<JobResponse>('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total && onUploadProgress) {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          onUploadProgress(percentCompleted);
        }
      },
    });

    return response.data;
  }

  /**
   * Get the status of a conversion job.
   * 
   * @param jobId - Unique job identifier
   * @returns Promise with job status
   */
  async getJobStatus(jobId: string): Promise<JobStatusResponse> {
    const response = await this.client.get<JobStatusResponse>(`/jobs/${jobId}`);
    return response.data;
  }

  /**
   * Download the converted Word document.
   * 
   * @param jobId - Unique job identifier
   * @returns Promise with file blob
   */
  async downloadFile(jobId: string): Promise<Blob> {
    const response = await this.client.get(`/download/${jobId}`, {
      responseType: 'blob',
    });

    return response.data;
  }
}

// Export singleton instance
export const api = new ConversionAPI();
export default ConversionAPI;
