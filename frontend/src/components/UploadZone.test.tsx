/**
 * Unit tests for UploadZone component.
 * 
 * Tests file selection, drag-and-drop, file validation, and upload trigger.
 * Requirements: 9.1, 9.2, 9.3
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import UploadZone from './UploadZone';

describe('UploadZone', () => {
  const mockOnFileSelected = jest.fn();

  beforeEach(() => {
    mockOnFileSelected.mockClear();
  });

  describe('Rendering', () => {
    it('should render upload zone with default state', () => {
      render(<UploadZone onFileSelected={mockOnFileSelected} />);
      
      expect(screen.getByText(/Drop your PDF here/i)).toBeInTheDocument();
      expect(screen.getByText(/or click to browse your files/i)).toBeInTheDocument();
      expect(screen.getByText(/PDF Files Only/i)).toBeInTheDocument();
      expect(screen.getByText(/Max 50MB/i)).toBeInTheDocument();
    });

    it('should render uploading state when isUploading is true', () => {
      render(<UploadZone onFileSelected={mockOnFileSelected} isUploading={true} />);
      
      expect(screen.getByText(/Uploading.../i)).toBeInTheDocument();
    });

    it('should have proper ARIA labels', () => {
      render(<UploadZone onFileSelected={mockOnFileSelected} />);
      
      expect(screen.getByRole('button', { name: /Upload PDF file/i })).toBeInTheDocument();
      expect(screen.getByLabelText(/File upload input/i)).toBeInTheDocument();
    });
  });

  describe('File Selection', () => {
    it('should call onFileSelected when a valid PDF is selected', async () => {
      render(<UploadZone onFileSelected={mockOnFileSelected} />);
      
      const file = new File(['dummy content'], 'test.pdf', { type: 'application/pdf' });
      const input = screen.getByLabelText(/File upload input/i) as HTMLInputElement;
      
      await userEvent.upload(input, file);
      
      await waitFor(() => {
        expect(mockOnFileSelected).toHaveBeenCalledWith(file);
      });
    });

    it('should not call onFileSelected when file is invalid type', async () => {
      render(<UploadZone onFileSelected={mockOnFileSelected} />);
      
      const file = new File(['dummy content'], 'test.txt', { type: 'text/plain' });
      const input = screen.getByLabelText(/File upload input/i) as HTMLInputElement;
      
      await userEvent.upload(input, file);
      
      await waitFor(() => {
        expect(screen.getByText(/Please upload a PDF file/i)).toBeInTheDocument();
      }, { timeout: 3000 });
      expect(mockOnFileSelected).not.toHaveBeenCalled();
    });

    it('should show error when file is too large', async () => {
      render(<UploadZone onFileSelected={mockOnFileSelected} />);
      
      // Create a file larger than 50MB
      const largeFile = new File(['x'.repeat(51 * 1024 * 1024)], 'large.pdf', { 
        type: 'application/pdf' 
      });
      const input = screen.getByLabelText(/File upload input/i) as HTMLInputElement;
      
      await userEvent.upload(input, largeFile);
      
      await waitFor(() => {
        expect(screen.getByText(/File size must be less than 50MB/i)).toBeInTheDocument();
      }, { timeout: 3000 });
      expect(mockOnFileSelected).not.toHaveBeenCalled();
    });
  });

  describe('Drag and Drop', () => {
    it('should show drag active state when file is dragged over', () => {
      render(<UploadZone onFileSelected={mockOnFileSelected} />);
      
      const dropzone = screen.getByRole('button', { name: /Upload PDF file/i });
      
      fireEvent.dragEnter(dropzone, {
        dataTransfer: {
          types: ['Files'],
          items: [{ kind: 'file', type: 'application/pdf' }],
        },
      });
      
      expect(screen.getByText(/Drop it like it's hot!/i)).toBeInTheDocument();
    });

    it('should call onFileSelected when valid PDF is dropped', async () => {
      render(<UploadZone onFileSelected={mockOnFileSelected} />);
      
      const file = new File(['dummy content'], 'test.pdf', { type: 'application/pdf' });
      const dropzone = screen.getByRole('button', { name: /Upload PDF file/i });
      
      fireEvent.drop(dropzone, {
        dataTransfer: {
          files: [file],
          types: ['Files'],
        },
      });
      
      await waitFor(() => {
        expect(mockOnFileSelected).toHaveBeenCalledWith(file);
      });
    });

    it('should show error when invalid file type is dropped', async () => {
      render(<UploadZone onFileSelected={mockOnFileSelected} />);
      
      const file = new File(['dummy content'], 'test.txt', { type: 'text/plain' });
      const dropzone = screen.getByRole('button', { name: /Upload PDF file/i });
      
      fireEvent.drop(dropzone, {
        dataTransfer: {
          files: [file],
          types: ['Files'],
        },
      });
      
      await waitFor(() => {
        expect(screen.getByText(/Please upload a PDF file/i)).toBeInTheDocument();
      });
      expect(mockOnFileSelected).not.toHaveBeenCalled();
    });
  });

  describe('Upload Trigger', () => {
    it('should trigger upload immediately after file selection', async () => {
      render(<UploadZone onFileSelected={mockOnFileSelected} />);
      
      const file = new File(['dummy content'], 'test.pdf', { type: 'application/pdf' });
      const input = screen.getByLabelText(/File upload input/i) as HTMLInputElement;
      
      await userEvent.upload(input, file);
      
      await waitFor(() => {
        expect(mockOnFileSelected).toHaveBeenCalledTimes(1);
        expect(mockOnFileSelected).toHaveBeenCalledWith(file);
      });
    });

    it('should not trigger upload when isUploading is true', async () => {
      render(<UploadZone onFileSelected={mockOnFileSelected} isUploading={true} />);
      
      const file = new File(['dummy content'], 'test.pdf', { type: 'application/pdf' });
      const input = screen.getByLabelText(/File upload input/i) as HTMLInputElement;
      
      // Try to upload
      await userEvent.upload(input, file);
      
      // Should not call onFileSelected because component is disabled
      expect(mockOnFileSelected).not.toHaveBeenCalled();
    });
  });

  describe('Error Display', () => {
    it('should display error message with proper ARIA attributes', async () => {
      render(<UploadZone onFileSelected={mockOnFileSelected} />);
      
      const file = new File(['dummy content'], 'test.txt', { type: 'text/plain' });
      const input = screen.getByLabelText(/File upload input/i) as HTMLInputElement;
      
      await userEvent.upload(input, file);
      
      await waitFor(() => {
        const errorAlert = screen.getByRole('alert');
        expect(errorAlert).toBeInTheDocument();
        expect(errorAlert).toHaveAttribute('aria-live', 'polite');
        expect(screen.getByText(/Please upload a PDF file/i)).toBeInTheDocument();
      }, { timeout: 3000 });
    });

    it('should clear previous error when new valid file is selected', async () => {
      render(<UploadZone onFileSelected={mockOnFileSelected} />);
      
      // First, upload invalid file
      const invalidFile = new File(['dummy'], 'test.txt', { type: 'text/plain' });
      const input = screen.getByLabelText(/File upload input/i) as HTMLInputElement;
      
      await userEvent.upload(input, invalidFile);
      
      await waitFor(() => {
        expect(screen.getByText(/Please upload a PDF file/i)).toBeInTheDocument();
      }, { timeout: 3000 });
      
      // Then, upload valid file
      const validFile = new File(['dummy'], 'test.pdf', { type: 'application/pdf' });
      await userEvent.upload(input, validFile);
      
      await waitFor(() => {
        expect(screen.queryByText(/Please upload a PDF file/i)).not.toBeInTheDocument();
        expect(mockOnFileSelected).toHaveBeenCalledWith(validFile);
      }, { timeout: 3000 });
    });
  });

  describe('Accessibility', () => {
    it('should be keyboard accessible', () => {
      render(<UploadZone onFileSelected={mockOnFileSelected} />);
      
      const dropzone = screen.getByRole('button', { name: /Upload PDF file/i });
      expect(dropzone).toHaveAttribute('tabIndex', '0');
    });

    it('should have proper role and aria-label', () => {
      render(<UploadZone onFileSelected={mockOnFileSelected} />);
      
      const dropzone = screen.getByRole('button');
      expect(dropzone).toHaveAttribute('aria-label', 'Upload PDF file');
    });
  });
});
