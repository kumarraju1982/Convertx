/**
 * Main App component for PDF to Word Converter.
 * 
 * Stunning modern UI with glassmorphism, gradients, and animations.
 */

import { useState, useEffect } from 'react';
import { FileText, Sparkles, Zap } from 'lucide-react';
import UploadZone from './components/UploadZone';
import ProgressDisplay from './components/ProgressDisplay';
import { api } from './services/api';
import { downloadConvertedFile } from './utils/download';

type AppState = 'idle' | 'uploading' | 'processing' | 'completed' | 'error';

function App() {
  const [state, setState] = useState<AppState>('idle');
  const [jobId, setJobId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });

  // Track mouse for gradient effect
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      setMousePosition({ x: e.clientX, y: e.clientY });
    };
    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  const handleFileSelected = async (file: File) => {
    setState('uploading');
    setError(null);
    setUploadProgress(0);

    try {
      const response = await api.uploadFile(file, (progress) => {
        setUploadProgress(progress);
      });
      setJobId(response.job_id);
      setState('processing');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to upload file');
      setState('error');
    }
  };

  const handleDownload = async (jobId: string, filename: string) => {
    try {
      await downloadConvertedFile(jobId, filename);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to download file');
    }
  };

  const handleReset = () => {
    setState('idle');
    setJobId(null);
    setError(null);
  };

  return (
    <div className="min-h-screen relative overflow-hidden">
      {/* Animated Background */}
      <div className="fixed inset-0 bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 animate-gradient-shift"></div>
      
      {/* Animated Orbs */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-400 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-blob"></div>
        <div className="absolute top-1/3 right-1/4 w-96 h-96 bg-purple-400 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-blob animation-delay-2000"></div>
        <div className="absolute bottom-1/4 left-1/3 w-96 h-96 bg-pink-400 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-blob animation-delay-4000"></div>
      </div>

      {/* Mouse Follower Gradient */}
      <div 
        className="fixed w-96 h-96 rounded-full pointer-events-none transition-all duration-300 ease-out"
        style={{
          background: 'radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%)',
          left: mousePosition.x - 192,
          top: mousePosition.y - 192,
        }}
      ></div>

      {/* Content Container */}
      <div className="relative z-10 min-h-screen flex flex-col">
        {/* Header */}
        <header className="backdrop-blur-md bg-white/10 border-b border-white/20 shadow-lg">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="relative">
                  <div className="absolute inset-0 bg-gradient-to-r from-blue-400 to-purple-500 rounded-xl blur-lg opacity-75 animate-pulse"></div>
                  <div className="relative bg-white/20 backdrop-blur-sm p-3 rounded-xl border border-white/30">
                    <FileText className="w-8 h-8 text-white" />
                  </div>
                </div>
                <div>
                  <h1 className="text-3xl font-bold text-white drop-shadow-lg flex items-center gap-2">
                    ConvertX
                    <Sparkles className="w-6 h-6 text-yellow-300 animate-pulse" />
                  </h1>
                  <p className="mt-1 text-sm text-white/90 font-medium flex items-center gap-1">
                    <Zap className="w-4 h-4 text-yellow-300" />
                    AI-Powered PDF to Word Conversion
                  </p>
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-12">
          {(state === 'idle' || state === 'uploading') && (
            <div className="animate-fade-in-up">
              <UploadZone
                onFileSelected={handleFileSelected}
                isUploading={state === 'uploading'}
              />
              {state === 'uploading' && (
                <div className="w-full max-w-2xl mx-auto mt-8 animate-fade-in-up animation-delay-200">
                  <div className="backdrop-blur-xl bg-white/10 rounded-3xl p-8 border border-white/20 shadow-2xl">
                    <div className="text-center">
                      <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-r from-blue-400 to-purple-500 rounded-full mb-4 animate-spin-slow">
                        <FileText className="w-8 h-8 text-white" />
                      </div>
                      <h3 className="text-2xl font-bold text-white mb-4">
                        Uploading Your File...
                      </h3>
                      <div className="relative w-full bg-white/10 rounded-full h-3 mb-3 overflow-hidden">
                        <div className="absolute inset-0 bg-gradient-to-r from-blue-400 via-purple-500 to-pink-500 animate-gradient-x"></div>
                        <div
                          className="relative bg-gradient-to-r from-blue-500 to-purple-600 h-3 rounded-full transition-all duration-300 shadow-lg"
                          style={{ width: `${uploadProgress}%` }}
                        />
                      </div>
                      <p className="text-lg font-semibold text-white/90">{uploadProgress}% Complete</p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {state === 'processing' && jobId && (
            <ProgressDisplay
              jobId={jobId}
              onDownload={handleDownload}
              onReset={handleReset}
            />
          )}

          {state === 'error' && error && (
            <div className="w-full max-w-2xl mx-auto animate-fade-in-up">
              <div className="backdrop-blur-xl bg-white/10 rounded-3xl p-8 border border-red-300/30 shadow-2xl">
                <div className="text-center">
                  <div className="inline-flex items-center justify-center w-16 h-16 bg-red-500/20 rounded-full mb-4">
                    <span className="text-4xl">⚠️</span>
                  </div>
                  <h3 className="text-2xl font-bold text-white mb-3">
                    Oops! Something Went Wrong
                  </h3>
                  <p className="text-white/80 mb-6 text-lg">{error}</p>
                  <button 
                    onClick={handleReset} 
                    className="px-8 py-4 bg-gradient-to-r from-blue-500 to-purple-600 text-white font-semibold rounded-xl hover:shadow-2xl hover:scale-105 transition-all duration-300 border border-white/20"
                  >
                    Try Again
                  </button>
                </div>
              </div>
            </div>
          )}
        </main>

        {/* Footer */}
        <footer className="backdrop-blur-md bg-white/5 border-t border-white/10">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
            <p className="text-center text-sm text-white/70 font-medium">
              ✨ Created by Raju Kumar ✨
            </p>
          </div>
        </footer>
      </div>
    </div>
  );
}

export default App;
