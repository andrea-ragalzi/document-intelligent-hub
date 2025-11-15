"use client";

import { useState, useEffect, useRef } from "react";

interface UploadProgressState {
  progress: number; // 0-100
  status: "uploading" | "processing" | "complete" | "error";
  message: string;
  estimatedTime: string;
  chunksProcessed: number;
  totalChunks: number;
}

interface UseUploadProgressOptions {
  isUploading: boolean;
  estimatedTotalTime?: number; // in seconds
  onComplete?: () => void;
}

/**
 * Hook to track and simulate upload progress with realistic timing
 *
 * Progress phases:
 * 1. Upload (0-10%): Fast, ~2-5 seconds
 * 2. Parsing PDF (10-20%): Medium, ~5-10 seconds
 * 3. Chunking (20-30%): Fast, ~2-3 seconds
 * 4. Embedding generation (30-95%): Slow, majority of time
 * 5. Database write (95-100%): Fast, ~2-3 seconds
 */
export const useUploadProgress = ({
  isUploading,
  estimatedTotalTime = 180, // Default 3 minutes for medium doc
  onComplete,
}: UseUploadProgressOptions) => {
  const [state, setState] = useState<UploadProgressState>({
    progress: 0,
    status: "uploading",
    message: "Preparing upload...",
    estimatedTime: "Calculating...",
    chunksProcessed: 0,
    totalChunks: 0,
  });

  const progressInterval = useRef<NodeJS.Timeout | null>(null);
  const startTime = useRef<number>(0);

  useEffect(() => {
    if (!isUploading) {
      // Reset when not uploading
      if (progressInterval.current) {
        clearInterval(progressInterval.current);
        progressInterval.current = null;
      }
      return;
    }

    // Start progress simulation
    startTime.current = Date.now();
    setState({
      progress: 0,
      status: "uploading",
      message: "Uploading document...",
      estimatedTime: formatTime(estimatedTotalTime),
      chunksProcessed: 0,
      totalChunks: 0,
    });

    // Update progress every 500ms
    progressInterval.current = setInterval(() => {
      const elapsed = (Date.now() - startTime.current) / 1000; // seconds
      const progressPercent = Math.min(
        95,
        (elapsed / estimatedTotalTime) * 100
      );

      // Determine status and message based on progress
      let status: UploadProgressState["status"] = "uploading";
      let message = "Uploading document...";

      if (progressPercent < 10) {
        status = "uploading";
        message = "Uploading PDF to server...";
      } else if (progressPercent < 20) {
        status = "processing";
        message = "Parsing PDF content...";
      } else if (progressPercent < 30) {
        status = "processing";
        message = "Splitting into chunks...";
      } else if (progressPercent < 95) {
        status = "processing";
        message = "Generating embeddings...";

        // Simulate chunks processing
        const estimatedTotalChunks = Math.floor((estimatedTotalTime / 5) * 95); // ~95 chunks/sec estimate
        const chunksProcessed = Math.floor(
          (progressPercent / 95) * estimatedTotalChunks
        );

        setState((prev) => ({
          ...prev,
          progress: progressPercent,
          status,
          message,
          estimatedTime: formatTime(estimatedTotalTime - elapsed),
          chunksProcessed,
          totalChunks: estimatedTotalChunks,
        }));
        return;
      } else {
        status = "processing";
        message = "Writing to database...";
      }

      const remaining = estimatedTotalTime - elapsed;

      setState((prev) => ({
        ...prev,
        progress: progressPercent,
        status,
        message,
        estimatedTime: formatTime(remaining > 0 ? remaining : 0),
      }));
    }, 500);

    return () => {
      if (progressInterval.current) {
        clearInterval(progressInterval.current);
        progressInterval.current = null;
      }
    };
  }, [isUploading, estimatedTotalTime]);

  // Mark as complete when upload finishes
  useEffect(() => {
    if (!isUploading && state.progress > 0 && state.status !== "complete") {
      setState((prev) => ({
        ...prev,
        progress: 100,
        status: "complete",
        message: "Upload and indexing complete!",
        estimatedTime: "Done",
      }));

      if (onComplete) {
        onComplete();
      }

      // Keep complete state for 2 seconds, then reset
      const timeout = setTimeout(() => {
        setState({
          progress: 0,
          status: "uploading",
          message: "",
          estimatedTime: "",
          chunksProcessed: 0,
          totalChunks: 0,
        });
      }, 3000);

      return () => clearTimeout(timeout);
    }
  }, [isUploading, state.progress, state.status, onComplete]);

  return state;
};

/**
 * Format seconds to human-readable time string
 */
function formatTime(seconds: number): string {
  if (seconds < 0) return "0s";
  if (seconds < 60) return `${Math.ceil(seconds)}s`;

  const minutes = Math.floor(seconds / 60);
  const secs = Math.ceil(seconds % 60);

  if (minutes < 60) {
    return `${minutes}m ${secs}s`;
  }

  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  return `${hours}h ${mins}m`;
}
