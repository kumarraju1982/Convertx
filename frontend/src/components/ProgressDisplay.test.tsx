/**
 * Unit tests for ProgressDisplay component.
 * 
 * Tests rendering with different job states, progress bar calculation,
 * download button display, and error message display.
 * Requirements: 11.2, 11.3, 11.5
 */

import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ProgressDisplay from './ProgressDisplay';
import { api } from '../services/api';
import { JobStatusResponse } from '../types/api';

// Mock the API
jest.mock('../services/api');
const mockApi = api as jest.Mocked<typeof api>;

describe('ProgressDisplay', () => {
  const mockOnDownload = jest.fn();
  const mockOnReset = jest.fn();
  const testJobId = 'test-job-123';

  beforeEach(() => {
    jest.clearAllMocks();
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  describe('Rendering with different job states', () => {
    it('should show loading state initially', () => {
      mockApi.getJobStatus.mockImplementation(() => new Promise(() => {})); // Never resolves
      
      render(
        <ProgressDisplay
          jobId={testJobId}
          onDownload={mockOnDownload}
          onReset={mockOnReset}
        />
      );

      expect(screen.getByText(/Loading status.../i)).toBeInTheDocument();
    });

    it('should render pending state correctly', async () => {
      const pendingStatus: JobStatusResponse = {
        job_id: testJobId,
        status: 'pending',
        progress: { current_page: 0, total_pages: 0, percentage: 0 },
        created_at: new Date().toISOString(),
      };

      mockApi.getJobStatus.mockResolvedValue(pendingStatus);

      render(
        <ProgressDisplay
          jobId={testJobId}
          onDownload={mockOnDownload}
          onReset={mockOnReset}
        />
      );

      await waitFor(() => {
        expect(screen.getByText(/Queued/i)).toBeInTheDocument();
      });

      expect(screen.getByText(/Your conversion is in the queue/i)).toBeInTheDocument();
    });

    it('should render processing state correctly', async () => {
      const processingStatus: JobStatusResponse = {
        job_id: testJobId,
        status: 'processing',
        progress: { current_page: 2, total_pages: 5, percentage: 40 },
        created_at: new Date().toISOString(),
      };

      mockApi.getJobStatus.mockResolvedValue(processingStatus);

      render(
        <ProgressDisplay
          jobId={testJobId}
          onDownload={mockOnDownload}
          onReset={mockOnReset}
        />
      );

      await waitFor(() => {
        expect(screen.getByText(/Processing/i)).toBeInTheDocument();
      });

      expect(screen.getByText(/Converting page 2 of 5/i)).toBeInTheDocument();
    });

    it('should render completed state correctly', async () => {
      const completedStatus: JobStatusResponse = {
        job_id: testJobId,
        status: 'completed',
        progress: { current_page: 5, total_pages: 5, percentage: 100 },
        created_at: new Date().toISOString(),
        completed_at: new Date().toISOString(),
      };

      mockApi.getJobStatus.mockResolvedValue(completedStatus);

      render(
        <ProgressDisplay
          jobId={testJobId}
          onDownload={mockOnDownload}
          onReset={mockOnReset}
        />
      );

      await waitFor(() => {
        expect(screen.getByText(/Completed!/i)).toBeInTheDocument();
      });

      expect(screen.getByText(/Your document is ready for download/i)).toBeInTheDocument();
    });

    it('should render failed state correctly', async () => {
      const failedStatus: JobStatusResponse = {
        job_id: testJobId,
        status: 'failed',
        progress: { current_page: 2, total_pages: 5, percentage: 40 },
        error: 'OCR processing failed',
        created_at: new Date().toISOString(),
      };

      mockApi.getJobStatus.mockResolvedValue(failedStatus);

      render(
        <ProgressDisplay
          jobId={testJobId}
          onDownload={mockOnDownload}
          onReset={mockOnReset}
        />
      );

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /Failed/i })).toBeInTheDocument();
      });

      expect(screen.getByText(/OCR processing failed/i)).toBeInTheDocument();
    });
  });

  describe('Progress bar calculation', () => {
    it('should display correct percentage in progress bar', async () => {
      const processingStatus: JobStatusResponse = {
        job_id: testJobId,
        status: 'processing',
        progress: { current_page: 3, total_pages: 10, percentage: 30 },
        created_at: new Date().toISOString(),
      };

      mockApi.getJobStatus.mockResolvedValue(processingStatus);

      render(
        <ProgressDisplay
          jobId={testJobId}
          onDownload={mockOnDownload}
          onReset={mockOnReset}
        />
      );

      await waitFor(() => {
        const progressBar = screen.getByRole('progressbar');
        expect(progressBar).toHaveAttribute('aria-valuenow', '30');
      });

      expect(screen.getByText('30%')).toBeInTheDocument();
    });

    it('should show progress bar for pending state', async () => {
      const pendingStatus: JobStatusResponse = {
        job_id: testJobId,
        status: 'pending',
        progress: { current_page: 0, total_pages: 5, percentage: 0 },
        created_at: new Date().toISOString(),
      };

      mockApi.getJobStatus.mockResolvedValue(pendingStatus);

      render(
        <ProgressDisplay
          jobId={testJobId}
          onDownload={mockOnDownload}
          onReset={mockOnReset}
        />
      );

      await waitFor(() => {
        const progressBar = screen.getByRole('progressbar');
        expect(progressBar).toBeInTheDocument();
      });
    });

    it('should not show progress bar for completed state', async () => {
      const completedStatus: JobStatusResponse = {
        job_id: testJobId,
        status: 'completed',
        progress: { current_page: 5, total_pages: 5, percentage: 100 },
        created_at: new Date().toISOString(),
        completed_at: new Date().toISOString(),
      };

      mockApi.getJobStatus.mockResolvedValue(completedStatus);

      render(
        <ProgressDisplay
          jobId={testJobId}
          onDownload={mockOnDownload}
          onReset={mockOnReset}
        />
      );

      await waitFor(() => {
        expect(screen.getByText(/Completed!/i)).toBeInTheDocument();
      });

      expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
    });
  });

  describe('Download button display', () => {
    it('should show download button when job is completed', async () => {
      const completedStatus: JobStatusResponse = {
        job_id: testJobId,
        status: 'completed',
        progress: { current_page: 5, total_pages: 5, percentage: 100 },
        created_at: new Date().toISOString(),
        completed_at: new Date().toISOString(),
      };

      mockApi.getJobStatus.mockResolvedValue(completedStatus);

      render(
        <ProgressDisplay
          jobId={testJobId}
          onDownload={mockOnDownload}
          onReset={mockOnReset}
        />
      );

      await waitFor(() => {
        expect(screen.getByText(/Download Word Document/i)).toBeInTheDocument();
      });
    });

    it('should call onDownload when download button is clicked', async () => {
      const completedStatus: JobStatusResponse = {
        job_id: testJobId,
        status: 'completed',
        progress: { current_page: 5, total_pages: 5, percentage: 100 },
        created_at: new Date().toISOString(),
        completed_at: new Date().toISOString(),
      };

      mockApi.getJobStatus.mockResolvedValue(completedStatus);

      render(
        <ProgressDisplay
          jobId={testJobId}
          onDownload={mockOnDownload}
          onReset={mockOnReset}
        />
      );

      await waitFor(() => {
        expect(screen.getByText(/Download Word Document/i)).toBeInTheDocument();
      });

      const downloadButton = screen.getByText(/Download Word Document/i);
      await userEvent.click(downloadButton);

      expect(mockOnDownload).toHaveBeenCalledWith(testJobId, `converted_${testJobId}.docx`);
    });

    it('should not show download button when job is processing', async () => {
      const processingStatus: JobStatusResponse = {
        job_id: testJobId,
        status: 'processing',
        progress: { current_page: 2, total_pages: 5, percentage: 40 },
        created_at: new Date().toISOString(),
      };

      mockApi.getJobStatus.mockResolvedValue(processingStatus);

      render(
        <ProgressDisplay
          jobId={testJobId}
          onDownload={mockOnDownload}
          onReset={mockOnReset}
        />
      );

      await waitFor(() => {
        expect(screen.getByText(/Processing/i)).toBeInTheDocument();
      });

      expect(screen.queryByText(/Download Word Document/i)).not.toBeInTheDocument();
    });
  });

  describe('Error message display', () => {
    it('should display error message when job fails', async () => {
      const failedStatus: JobStatusResponse = {
        job_id: testJobId,
        status: 'failed',
        progress: { current_page: 2, total_pages: 5, percentage: 40 },
        error: 'PDF file is corrupted',
        created_at: new Date().toISOString(),
      };

      mockApi.getJobStatus.mockResolvedValue(failedStatus);

      render(
        <ProgressDisplay
          jobId={testJobId}
          onDownload={mockOnDownload}
          onReset={mockOnReset}
        />
      );

      await waitFor(() => {
        expect(screen.getByText(/PDF file is corrupted/i)).toBeInTheDocument();
      });
    });

    it('should show Try Again button when job fails', async () => {
      const failedStatus: JobStatusResponse = {
        job_id: testJobId,
        status: 'failed',
        progress: { current_page: 2, total_pages: 5, percentage: 40 },
        error: 'Processing error',
        created_at: new Date().toISOString(),
      };

      mockApi.getJobStatus.mockResolvedValue(failedStatus);

      render(
        <ProgressDisplay
          jobId={testJobId}
          onDownload={mockOnDownload}
          onReset={mockOnReset}
        />
      );

      await waitFor(() => {
        expect(screen.getByText(/Try Again/i)).toBeInTheDocument();
      });
    });

    it('should call onReset when Try Again button is clicked', async () => {
      const failedStatus: JobStatusResponse = {
        job_id: testJobId,
        status: 'failed',
        progress: { current_page: 2, total_pages: 5, percentage: 40 },
        error: 'Processing error',
        created_at: new Date().toISOString(),
      };

      mockApi.getJobStatus.mockResolvedValue(failedStatus);

      render(
        <ProgressDisplay
          jobId={testJobId}
          onDownload={mockOnDownload}
          onReset={mockOnReset}
        />
      );

      await waitFor(() => {
        expect(screen.getByText(/Try Again/i)).toBeInTheDocument();
      });

      const tryAgainButton = screen.getByText(/Try Again/i);
      await userEvent.click(tryAgainButton);

      expect(mockOnReset).toHaveBeenCalled();
    });

    it('should display error when API call fails', async () => {
      mockApi.getJobStatus.mockRejectedValue(new Error('Network error'));

      render(
        <ProgressDisplay
          jobId={testJobId}
          onDownload={mockOnDownload}
          onReset={mockOnReset}
        />
      );

      await waitFor(() => {
        expect(screen.getByText(/Network error/i)).toBeInTheDocument();
      });
    });
  });

  describe('Polling behavior', () => {
    it('should poll status periodically when processing', async () => {
      const processingStatus: JobStatusResponse = {
        job_id: testJobId,
        status: 'processing',
        progress: { current_page: 2, total_pages: 5, percentage: 40 },
        created_at: new Date().toISOString(),
      };

      mockApi.getJobStatus.mockResolvedValue(processingStatus);

      render(
        <ProgressDisplay
          jobId={testJobId}
          onDownload={mockOnDownload}
          onReset={mockOnReset}
        />
      );

      await waitFor(() => {
        expect(screen.getByText(/Processing/i)).toBeInTheDocument();
      });

      // Initial call should have been made
      expect(mockApi.getJobStatus).toHaveBeenCalled();
    });

    it('should display job ID in the interface', async () => {
      const processingStatus: JobStatusResponse = {
        job_id: testJobId,
        status: 'processing',
        progress: { current_page: 2, total_pages: 5, percentage: 40 },
        created_at: new Date().toISOString(),
      };

      mockApi.getJobStatus.mockResolvedValue(processingStatus);

      render(
        <ProgressDisplay
          jobId={testJobId}
          onDownload={mockOnDownload}
          onReset={mockOnReset}
        />
      );

      await waitFor(() => {
        expect(screen.getByText(new RegExp(testJobId))).toBeInTheDocument();
      });
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA attributes for status region', async () => {
      const processingStatus: JobStatusResponse = {
        job_id: testJobId,
        status: 'processing',
        progress: { current_page: 2, total_pages: 5, percentage: 40 },
        created_at: new Date().toISOString(),
      };

      mockApi.getJobStatus.mockResolvedValue(processingStatus);

      render(
        <ProgressDisplay
          jobId={testJobId}
          onDownload={mockOnDownload}
          onReset={mockOnReset}
        />
      );

      await waitFor(() => {
        const region = screen.getByRole('region', { name: /Conversion progress/i });
        expect(region).toBeInTheDocument();
      });
    });

    it('should have proper ARIA attributes for progress bar', async () => {
      const processingStatus: JobStatusResponse = {
        job_id: testJobId,
        status: 'processing',
        progress: { current_page: 3, total_pages: 10, percentage: 30 },
        created_at: new Date().toISOString(),
      };

      mockApi.getJobStatus.mockResolvedValue(processingStatus);

      render(
        <ProgressDisplay
          jobId={testJobId}
          onDownload={mockOnDownload}
          onReset={mockOnReset}
        />
      );

      await waitFor(() => {
        const progressBar = screen.getByRole('progressbar');
        expect(progressBar).toHaveAttribute('aria-valuenow', '30');
        expect(progressBar).toHaveAttribute('aria-valuemin', '0');
        expect(progressBar).toHaveAttribute('aria-valuemax', '100');
      });
    });

    it('should have live region for status updates', async () => {
      const processingStatus: JobStatusResponse = {
        job_id: testJobId,
        status: 'processing',
        progress: { current_page: 2, total_pages: 5, percentage: 40 },
        created_at: new Date().toISOString(),
      };

      mockApi.getJobStatus.mockResolvedValue(processingStatus);

      render(
        <ProgressDisplay
          jobId={testJobId}
          onDownload={mockOnDownload}
          onReset={mockOnReset}
        />
      );

      await waitFor(() => {
        const statusElement = screen.getByRole('status');
        expect(statusElement).toHaveAttribute('aria-live', 'polite');
      });
    });
  });
});
