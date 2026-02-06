import { useState, useRef, useCallback } from 'react';
import { Upload, FileText, Loader2, AlertCircle, CheckCircle } from 'lucide-react';
import { documentApi, pipelineApi } from '../services/api';
import type { Document } from '../types';

interface DocumentUploadProps {
  userId: string;
  onComplete: (document: Document, threads: unknown[]) => void;
}

type UploadStage =
  | 'idle'
  | 'uploading'
  | 'parsing'
  | 'generating-annotations'
  | 'forming-seeds'
  | 'generating-threads'
  | 'complete'
  | 'error';

const STAGE_MESSAGES: Record<UploadStage, string> = {
  idle: '',
  uploading: 'Uploading PDF...',
  parsing: 'Parsing document with GROBID...',
  'generating-annotations': 'AI agents are reading the document...',
  'forming-seeds': 'Finding discussion topics...',
  'generating-threads': 'Generating discussions...',
  complete: 'Complete!',
  error: 'An error occurred',
};

export function DocumentUpload({ userId, onComplete }: DocumentUploadProps) {
  const [stage, setStage] = useState<UploadStage>('idle');
  const [error, setError] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = useCallback((file: File) => {
    if (file.type !== 'application/pdf') {
      setError('Please select a PDF file');
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setError('File size must be less than 10MB');
      return;
    }
    setSelectedFile(file);
    setError(null);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFileSelect(file);
    },
    [handleFileSelect]
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleUpload = async () => {
    if (!selectedFile) return;

    try {
      setError(null);

      // Stage 1: Upload and parse PDF
      setStage('uploading');
      await new Promise((r) => setTimeout(r, 500)); // Brief pause for UX
      setStage('parsing');

      const document = await documentApi.upload(selectedFile, userId);
      console.log('[Upload] Document parsed:', document.documentId);
      console.log('[Upload] Sections:', document.parsedContent?.sections?.length);

      // Stage 2-4: Run pipeline
      setStage('generating-annotations');
      await new Promise((r) => setTimeout(r, 1000)); // Give visual feedback

      setStage('forming-seeds');
      await new Promise((r) => setTimeout(r, 500));

      setStage('generating-threads');
      const pipelineResult = await pipelineApi.generateDiscussions(document.documentId, {
        maxAnnotationsPerAgent: 12,
        targetSeeds: 5,
        turnsPerDiscussion: 4,
      });

      console.log('[Pipeline] Complete:', pipelineResult);
      console.log('[Pipeline] Threads generated:', pipelineResult.threads.length);

      setStage('complete');
      await new Promise((r) => setTimeout(r, 500));

      // Pass results to parent
      onComplete(document, pipelineResult.threads);
    } catch (err) {
      console.error('[Upload] Error:', err);
      setStage('error');
      setError(
        err instanceof Error
          ? err.message
          : 'An error occurred while processing the document'
      );
    }
  };

  const isProcessing = stage !== 'idle' && stage !== 'error' && stage !== 'complete';

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-50 p-8">
      <div className="w-full max-w-md">
        {/* Title */}
        <div className="text-center mb-8">
          <h1 className="text-2xl font-medium text-gray-900 mb-2">CoRead</h1>
          <p className="text-sm text-gray-500">
            Upload a PDF to start a multi-perspective reading discussion
          </p>
        </div>

        {/* Upload Card */}
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          {/* Drop Zone */}
          <div
            className={`
              border-2 border-dashed rounded-lg p-8 text-center transition-colors
              ${isDragging ? 'border-blue-400 bg-blue-50' : 'border-gray-200'}
              ${isProcessing ? 'pointer-events-none opacity-60' : 'cursor-pointer hover:border-gray-300'}
            `}
            onClick={() => !isProcessing && fileInputRef.current?.click()}
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf"
              className="hidden"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) handleFileSelect(file);
              }}
              disabled={isProcessing}
            />

            {selectedFile ? (
              <div className="flex flex-col items-center gap-3">
                <FileText className="w-12 h-12 text-gray-400" />
                <div>
                  <p className="text-sm font-medium text-gray-900">{selectedFile.name}</p>
                  <p className="text-xs text-gray-500">
                    {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center gap-3">
                <Upload className="w-12 h-12 text-gray-300" />
                <div>
                  <p className="text-sm text-gray-600">
                    Drop your PDF here or <span className="text-blue-500">browse</span>
                  </p>
                  <p className="text-xs text-gray-400 mt-1">Max 10MB</p>
                </div>
              </div>
            )}
          </div>

          {/* Processing Status */}
          {isProcessing && (
            <div className="mt-6 flex items-center gap-3 p-4 bg-gray-50 rounded-lg">
              <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-700">
                  {STAGE_MESSAGES[stage]}
                </p>
                <div className="mt-2 h-1 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-blue-500 transition-all duration-500"
                    style={{
                      width: `${
                        stage === 'uploading'
                          ? 10
                          : stage === 'parsing'
                          ? 25
                          : stage === 'generating-annotations'
                          ? 50
                          : stage === 'forming-seeds'
                          ? 70
                          : stage === 'generating-threads'
                          ? 90
                          : 100
                      }%`,
                    }}
                  />
                </div>
              </div>
            </div>
          )}

          {/* Success Status */}
          {stage === 'complete' && (
            <div className="mt-6 flex items-center gap-3 p-4 bg-green-50 rounded-lg">
              <CheckCircle className="w-5 h-5 text-green-500" />
              <p className="text-sm font-medium text-green-700">
                Document processed successfully!
              </p>
            </div>
          )}

          {/* Error Status */}
          {error && (
            <div className="mt-6 flex items-start gap-3 p-4 bg-red-50 rounded-lg">
              <AlertCircle className="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-red-700">Error</p>
                <p className="text-sm text-red-600 mt-1">{error}</p>
              </div>
            </div>
          )}

          {/* Upload Button */}
          <button
            onClick={handleUpload}
            disabled={!selectedFile || isProcessing}
            className={`
              mt-6 w-full py-3 px-4 rounded-lg text-sm font-medium transition-colors
              ${
                !selectedFile || isProcessing
                  ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  : 'bg-gray-900 text-white hover:bg-gray-800'
              }
            `}
          >
            {isProcessing ? 'Processing...' : 'Start Analysis'}
          </button>
        </div>

        {/* Footer */}
        <p className="text-xs text-gray-400 text-center mt-6">
          Your document will be analyzed by AI agents with different reading perspectives
        </p>
      </div>
    </div>
  );
}
