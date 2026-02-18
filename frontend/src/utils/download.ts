/**
 * Utility functions for file downloads.
 */

import { api } from '../services/api';

/**
 * Download a converted Word document.
 * 
 * @param jobId - Unique job identifier
 * @param filename - Desired filename for download
 */
export async function downloadConvertedFile(jobId: string, filename: string): Promise<void> {
  try {
    // Fetch the file blob from API
    const blob = await api.downloadFile(jobId);

    // Create a blob URL
    const url = window.URL.createObjectURL(blob);

    // Create a temporary anchor element and trigger download
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();

    // Clean up
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  } catch (error) {
    throw new Error(
      error instanceof Error ? error.message : 'Failed to download file'
    );
  }
}
