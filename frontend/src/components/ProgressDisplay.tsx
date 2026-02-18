/**
 * ProgressDisplay component with stunning glassmorphism design.
 * 
 * Displays job status, animated progress bar, and download button when complete.
 * Polls job status every 1.5 seconds with beautiful visual feedback.
 */

import { useEffect, useState } from 'react';
import { CheckCircle, XCircle, Loader2, Download, FileText, Sparkles, Zap, Clock } from 'lucide-react';
import React from 'react';
import { api } from '../services/api';
import { JobStatusResponse } from '../types/api';

interface ProgressDisplayProps {
  jobId: string;
  onDownload: (jobId: string, filename: string) => void;
  onReset: () => void;
}

const ProgressDisplay: React.FC<ProgressDisplayProps> = ({ jobId, onDownload, onReset }) => {
  const [status, setStatus] = useState<JobStatusResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isPolling, setIsPolling] = useState(true);
  const [pollCount, setPollCount] = useState(0);

  useEffect(() => {
    let intervalId: NodeJS.Timeout;

    const pollStatus = async () => {
      try {
        const response = await api.getJobStatus(jobId);
        setStatus(response);
        setError(null);
        setPollCount(prev => prev + 1);

        // Stop polling if job is completed or failed
        if (response.status === 'completed' || response.status === 'failed') {
          setIsPolling(false);
        }
        
        // If stuck in pending for more than 20 polls (30 seconds), show error
        if (response.status === 'pending' && pollCount > 20) {
          setError('Job is stuck in pending state. Please ensure Redis and Celery worker are running.');
          setIsPolling(false);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch status');
        setIsPolling(false);
      }
    };

    // Initial poll
    pollStatus();

    // Set up polling interval
    if (isPolling) {
      intervalId = setInterval(pollStatus, 1500); // Poll every 1.5 seconds
    }

    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [jobId, isPolling, pollCount]);

  const handleDownload = () => {
    if (status) {
      onDownload(jobId, `converted_${jobId}.docx`);
    }
  };

  if (error) {
    return (
      <div className="w-full max-w-3xl mx-auto animate-fade-in-up">
        <div className="relative backdrop-blur-xl bg-red-500/20 rounded-3xl p-10 border-2 border-red-400/50 shadow-2xl">
          {/* Animated Background */}
          <div className="absolute inset-0 rounded-3xl overflow-hidden pointer-events-none">
            <div className="absolute inset-0 bg-gradient-to-r from-red-500/10 via-pink-500/10 to-red-500/10 animate-gradient-x"></div>
          </div>

          <div className="relative flex flex-col items-center text-center space-y-6">
            <div className="relative">
              <div className="absolute inset-0 bg-red-400 rounded-full blur-2xl opacity-50 animate-pulse"></div>
              <div className="relative bg-white/20 backdrop-blur-sm p-6 rounded-3xl border border-white/30">
                <XCircle className="w-20 h-20 text-white drop-shadow-lg" />
              </div>
            </div>
            <div>
              <h3 className="text-3xl font-bold text-white drop-shadow-lg mb-3">Oops! Something went wrong</h3>
              <p className="text-xl text-white/90 max-w-md">{error}</p>
            </div>
            <button
              onClick={onReset}
              className="btn-secondary mt-4"
            >
              Try Again
            </button>
          </div>

          {/* Corner Decorations */}
          <div className="absolute top-4 left-4 w-8 h-8 border-t-2 border-l-2 border-white/30 rounded-tl-lg"></div>
          <div className="absolute top-4 right-4 w-8 h-8 border-t-2 border-r-2 border-white/30 rounded-tr-lg"></div>
          <div className="absolute bottom-4 left-4 w-8 h-8 border-b-2 border-l-2 border-white/30 rounded-bl-lg"></div>
          <div className="absolute bottom-4 right-4 w-8 h-8 border-b-2 border-r-2 border-white/30 rounded-br-lg"></div>
        </div>
      </div>
    );
  }

  if (!status) {
    return (
      <div className="w-full max-w-3xl mx-auto animate-fade-in-up">
        <div className="relative backdrop-blur-xl bg-white/10 rounded-3xl p-10 border border-white/20 shadow-2xl">
          <div className="flex flex-col items-center justify-center space-y-4">
            <div className="relative">
              <div className="absolute inset-0 bg-blue-400 rounded-full blur-2xl opacity-50 animate-pulse"></div>
              <Loader2 className="relative w-16 h-16 text-white animate-spin drop-shadow-lg" />
            </div>
            <p className="text-2xl font-semibold text-white">Loading status...</p>
          </div>
        </div>
      </div>
    );
  }

  const percentage = status.progress?.percentage || 0;

  return (
    <div className="w-full max-w-3xl mx-auto animate-fade-in-up" role="region" aria-label="Conversion progress">
      <div className="relative backdrop-blur-xl bg-white/10 rounded-3xl p-10 border border-white/20 shadow-2xl">
        {/* Animated Background Gradient */}
        <div className="absolute inset-0 rounded-3xl overflow-hidden pointer-events-none">
          <div className="absolute inset-0 bg-gradient-to-r from-blue-500/10 via-purple-500/10 to-pink-500/10 animate-gradient-x"></div>
        </div>

        <div className="relative">
          {/* Status Header */}
          <div className="flex flex-col items-center text-center space-y-6 mb-8" role="status" aria-live="polite">
            {status.status === 'pending' && (
              <>
                <div className="relative">
                  <div className="absolute inset-0 bg-yellow-400 rounded-full blur-2xl opacity-50 animate-pulse"></div>
                  <div className="relative bg-white/20 backdrop-blur-sm p-6 rounded-3xl border border-white/30">
                    <Clock className="w-20 h-20 text-white drop-shadow-lg animate-pulse" />
                  </div>
                </div>
                <div>
                  <div className="flex items-center justify-center gap-2 mb-2">
                    <h3 className="text-4xl font-bold text-white drop-shadow-lg">Queued</h3>
                    <Sparkles className="w-8 h-8 text-yellow-300 animate-pulse" />
                  </div>
                  <p className="text-xl text-white/90">Your conversion is in the queue ⏳</p>
                </div>
              </>
            )}

            {status.status === 'processing' && (
              <>
                <div className="relative">
                  <div className="absolute inset-0 bg-blue-400 rounded-full blur-2xl opacity-50 animate-pulse"></div>
                  <div className="relative bg-white/20 backdrop-blur-sm p-6 rounded-3xl border border-white/30 animate-scale-pulse">
                    <Zap className="w-20 h-20 text-white drop-shadow-lg" />
                  </div>
                </div>
                <div>
                  <div className="flex items-center justify-center gap-2 mb-2">
                    <h3 className="text-4xl font-bold text-white drop-shadow-lg">Processing</h3>
                    <Loader2 className="w-8 h-8 text-white animate-spin" />
                  </div>
                  <p className="text-xl text-white/90">
                    Converting page {status.progress?.current_page || 0} of {status.progress?.total_pages || 0} ⚡
                  </p>
                </div>
              </>
            )}

            {status.status === 'completed' && (
              <>
                <div className="relative">
                  <div className="absolute inset-0 bg-green-400 rounded-full blur-2xl opacity-50 animate-pulse"></div>
                  <div className="relative bg-white/20 backdrop-blur-sm p-6 rounded-3xl border border-white/30 animate-scale-pulse">
                    <CheckCircle className="w-20 h-20 text-white drop-shadow-lg" />
                  </div>
                </div>
                <div>
                  <div className="flex items-center justify-center gap-2 mb-2">
                    <h3 className="text-4xl font-bold text-white drop-shadow-lg">Completed!</h3>
                    <Sparkles className="w-8 h-8 text-yellow-300 animate-pulse" />
                  </div>
                  <p className="text-xl text-white/90">Your document is ready for download 🎉</p>
                </div>
              </>
            )}

            {status.status === 'failed' && (
              <>
                <div className="relative">
                  <div className="absolute inset-0 bg-red-400 rounded-full blur-2xl opacity-50 animate-pulse"></div>
                  <div className="relative bg-white/20 backdrop-blur-sm p-6 rounded-3xl border border-white/30">
                    <XCircle className="w-20 h-20 text-white drop-shadow-lg" />
                  </div>
                </div>
                <div>
                  <h3 className="text-4xl font-bold text-white drop-shadow-lg mb-2">Failed</h3>
                  <p className="text-xl text-white/90">{status.error || 'Conversion failed'} 😞</p>
                </div>
              </>
            )}
          </div>

          {/* Progress Bar */}
          {(status.status === 'processing' || status.status === 'pending') && (
            <div className="mb-8" role="progressbar" aria-valuenow={percentage} aria-valuemin={0} aria-valuemax={100}>
              <div className="flex justify-between text-lg font-semibold text-white mb-3">
                <span>Progress</span>
                <span className="text-2xl">{percentage}%</span>
              </div>
              <div className="relative w-full h-6 bg-white/20 backdrop-blur-sm rounded-full overflow-hidden border border-white/30 shadow-inner">
                <div
                  className="absolute inset-0 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 rounded-full transition-all duration-500 ease-out shadow-lg"
                  style={{ width: `${percentage}%` }}
                  aria-label={`${percentage}% complete`}
                >
                  <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent animate-shimmer"></div>
                </div>
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row gap-4">
            {status.status === 'completed' && (
              <>
                <button
                  onClick={handleDownload}
                  className="btn-primary flex items-center justify-center space-x-2 flex-1 text-lg"
                >
                  <Download className="w-6 h-6" />
                  <span>Download Word Document</span>
                </button>
                <button
                  onClick={onReset}
                  className="btn-secondary text-lg"
                >
                  Convert Another
                </button>
              </>
            )}

            {status.status === 'failed' && (
              <button
                onClick={onReset}
                className="btn-secondary w-full text-lg"
              >
                Try Again
              </button>
            )}
          </div>

          {/* Job Info */}
          <div className="mt-8 pt-6 border-t border-white/20">
            <div className="flex items-center justify-center space-x-2 text-sm text-white/70">
              <FileText className="w-4 h-4" />
              <span>Job ID: {jobId}</span>
            </div>
          </div>
        </div>

        {/* Corner Decorations */}
        <div className="absolute top-4 left-4 w-8 h-8 border-t-2 border-l-2 border-white/30 rounded-tl-lg"></div>
        <div className="absolute top-4 right-4 w-8 h-8 border-t-2 border-r-2 border-white/30 rounded-tr-lg"></div>
        <div className="absolute bottom-4 left-4 w-8 h-8 border-b-2 border-l-2 border-white/30 rounded-bl-lg"></div>
        <div className="absolute bottom-4 right-4 w-8 h-8 border-b-2 border-r-2 border-white/30 rounded-br-lg"></div>
      </div>
    </div>
  );
};

export default ProgressDisplay;
