/**
 * UploadZone component with stunning drag-and-drop functionality.
 * 
 * Modern glassmorphism design with 3D effects and animations.
 */

import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, AlertCircle, Sparkles } from 'lucide-react';

interface UploadZoneProps {
  onFileSelected: (file: File) => void;
  isUploading?: boolean;
}

const UploadZone: React.FC<UploadZoneProps> = ({ onFileSelected, isUploading = false }) => {
  const [error, setError] = useState<string | null>(null);

  const onDrop = useCallback(
    (acceptedFiles: File[], rejectedFiles: any[]) => {
      setError(null);

      if (rejectedFiles.length > 0) {
        const rejection = rejectedFiles[0];
        if (rejection.errors[0]?.code === 'file-invalid-type') {
          setError('Please upload a PDF file');
        } else if (rejection.errors[0]?.code === 'file-too-large') {
          setError('File size must be less than 50MB');
        } else {
          setError('Invalid file');
        }
        return;
      }

      if (acceptedFiles.length > 0) {
        onFileSelected(acceptedFiles[0]);
      }
    },
    [onFileSelected]
  );

  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
    },
    maxSize: 50 * 1024 * 1024, // 50MB
    multiple: false,
    disabled: isUploading,
  });

  return (
    <div className="w-full max-w-3xl mx-auto">
      <div
        {...getRootProps()}
        className={`
          relative backdrop-blur-xl rounded-3xl p-16 text-center cursor-pointer
          transition-all duration-300 ease-out transform
          border-2 border-dashed
          ${isDragActive && !isDragReject 
            ? 'border-blue-400 bg-blue-500/20 scale-105 shadow-2xl' 
            : ''
          }
          ${isDragReject 
            ? 'border-red-400 bg-red-500/20 scale-95' 
            : ''
          }
          ${!isDragActive && !isDragReject 
            ? 'border-white/30 bg-white/10 hover:border-white/50 hover:bg-white/20 hover:scale-102 hover:shadow-2xl' 
            : ''
          }
          ${isUploading ? 'opacity-50 cursor-not-allowed' : ''}
        `}
        role="button"
        aria-label="Upload PDF file"
        tabIndex={0}
      >
        <input {...getInputProps()} aria-label="File upload input" />

        {/* Animated Background Gradient */}
        <div className="absolute inset-0 rounded-3xl overflow-hidden pointer-events-none">
          <div className="absolute inset-0 bg-gradient-to-r from-blue-500/10 via-purple-500/10 to-pink-500/10 animate-gradient-x"></div>
        </div>

        <div className="relative flex flex-col items-center space-y-6">
          {isDragActive && !isDragReject ? (
            <>
              <div className="relative">
                <div className="absolute inset-0 bg-blue-400 rounded-full blur-2xl opacity-50 animate-pulse"></div>
                <Upload className="relative w-24 h-24 text-white animate-bounce drop-shadow-2xl" />
              </div>
              <div>
                <p className="text-3xl font-bold text-white drop-shadow-lg">Drop it like it's hot! 🔥</p>
                <p className="text-lg text-white/80 mt-2">Release to upload your PDF</p>
              </div>
            </>
          ) : isDragReject ? (
            <>
              <div className="relative">
                <div className="absolute inset-0 bg-red-400 rounded-full blur-2xl opacity-50"></div>
                <AlertCircle className="relative w-24 h-24 text-white animate-pulse" />
              </div>
              <div>
                <p className="text-3xl font-bold text-white drop-shadow-lg">Oops! Wrong file type</p>
                <p className="text-lg text-white/80 mt-2">Only PDF files are accepted</p>
              </div>
            </>
          ) : (
            <>
              <div className="relative group">
                <div className="absolute inset-0 bg-gradient-to-r from-blue-400 to-purple-500 rounded-full blur-2xl opacity-50 group-hover:opacity-75 transition-opacity animate-pulse"></div>
                <div className="relative bg-white/20 backdrop-blur-sm p-8 rounded-3xl border border-white/30 group-hover:scale-110 transition-transform duration-300">
                  <FileText className="w-20 h-20 text-white drop-shadow-lg" />
                </div>
              </div>
              <div className="space-y-3">
                <div className="flex items-center justify-center gap-2">
                  <p className="text-3xl font-bold text-white drop-shadow-lg">
                    {isUploading ? 'Uploading...' : 'Drop your PDF here'}
                  </p>
                  <Sparkles className="w-8 h-8 text-yellow-300 animate-pulse" />
                </div>
                <p className="text-xl text-white/90 font-medium">
                  or click to browse your files
                </p>
                <div className="flex items-center justify-center gap-4 mt-4">
                  <div className="px-4 py-2 bg-white/10 backdrop-blur-sm rounded-full border border-white/20">
                    <p className="text-sm text-white/80 font-medium">
                      📄 PDF Files Only
                    </p>
                  </div>
                  <div className="px-4 py-2 bg-white/10 backdrop-blur-sm rounded-full border border-white/20">
                    <p className="text-sm text-white/80 font-medium">
                      📦 Max 50MB
                    </p>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>

        {/* Corner Decorations */}
        <div className="absolute top-4 left-4 w-8 h-8 border-t-2 border-l-2 border-white/30 rounded-tl-lg"></div>
        <div className="absolute top-4 right-4 w-8 h-8 border-t-2 border-r-2 border-white/30 rounded-tr-lg"></div>
        <div className="absolute bottom-4 left-4 w-8 h-8 border-b-2 border-l-2 border-white/30 rounded-bl-lg"></div>
        <div className="absolute bottom-4 right-4 w-8 h-8 border-b-2 border-r-2 border-white/30 rounded-br-lg"></div>
      </div>

      {error && (
        <div 
          className="mt-6 backdrop-blur-xl bg-red-500/20 border-2 border-red-400/50 rounded-2xl p-6 flex items-start space-x-4 animate-fade-in-up shadow-2xl"
          role="alert"
          aria-live="polite"
        >
          <div className="flex-shrink-0">
            <div className="relative">
              <div className="absolute inset-0 bg-red-400 rounded-full blur-lg opacity-50"></div>
              <AlertCircle className="relative w-8 h-8 text-white" aria-hidden="true" />
            </div>
          </div>
          <div>
            <p className="text-lg font-semibold text-white">Error</p>
            <p className="text-white/90 mt-1">{error}</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default UploadZone;
