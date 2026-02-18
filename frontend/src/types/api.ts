/**
 * TypeScript interfaces for API types.
 * 
 * These types match the API responses from the Flask backend.
 */

export interface JobResponse {
  job_id: string;
  status: JobStatus;
  message: string;
}

export type JobStatus = 'pending' | 'processing' | 'completed' | 'failed';

export interface JobStatusResponse {
  job_id: string;
  status: JobStatus;
  progress: {
    current_page: number;
    total_pages: number;
    percentage: number;
  };
  error?: string;
  created_at: string;
  completed_at?: string;
}

export interface ApiError {
  error: string;
  message: string;
  details?: Record<string, unknown>;
}
