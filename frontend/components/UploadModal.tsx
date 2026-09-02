"use client";

import { X, Upload, FileText } from "lucide-react";
import { FormEvent, ChangeEvent, useState, DragEvent, useEffect } from "react";
import { UploadProgress } from "./UploadProgress";
import { AlertMessage } from "./AlertMessage";
import { LanguageSelector } from "./LanguageSelector";
import type { AlertState } from "@/lib/types";

interface UploadProgressState {
  progress: number;
  status: "uploading" | "processing" | "complete" | "error";
  message?: string;
  estimatedTime?: string;
  chunksProcessed?: number;
  totalChunks?: number;
  currentPhase?: "upload" | "embedding";
}

interface UploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  file: File | null;
  isUploading: boolean;
  uploadAlert: AlertState;
  onFileChange: (e: ChangeEvent<HTMLInputElement>) => void;
  onUpload: (e: FormEvent) => void;
  uploadProgress?: UploadProgressState;
  selectedLanguage: string;
  onLanguageChange: (lang: string) => void;
}

export const UploadModal: React.FC<UploadModalProps> = ({
  isOpen,
  onClose,
  file,
  isUploading,
  uploadAlert,
  onFileChange,
  onUpload,
  uploadProgress,
  selectedLanguage,
  onLanguageChange,
}) => {
  const [isDragging, setIsDragging] = useState(false);

  // Prevent closing with ESC key during upload
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen && !isUploading) {
        onClose();
      }
    };
    document.addEventListener("keydown", handleEscape);
    return () => document.removeEventListener("keydown", handleEscape);
  }, [isOpen, isUploading, onClose]);

  if (!isOpen) return null;

  const handleDragEvents = (
    e: DragEvent<HTMLButtonElement>,
    action: "enter" | "leave" | "over"
  ) => {
    e.preventDefault();
    e.stopPropagation();
    if (action === "enter") setIsDragging(true);
    if (action === "leave") setIsDragging(false);
  };

  const handleDrop = (e: DragEvent<HTMLButtonElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const droppedFiles = e.dataTransfer.files;
    if (droppedFiles.length > 0 && droppedFiles[0].type === "application/pdf") {
      const syntheticEvent = {
        target: { files: droppedFiles },
      } as ChangeEvent<HTMLInputElement>;
      onFileChange(syntheticEvent);
    }
  };

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    onUpload(e);
  };

  const handleOverlayClick = () => {
    if (!isUploading) onClose();
  };

  const overlayClassName = `fixed inset-0 bg-black/60 z-50 transition-opacity duration-300 ${
    isUploading ? "cursor-not-allowed" : "cursor-pointer"
  }`;

  const dropZoneClassName = `relative border-2 border-dashed rounded-xl p-8 transition-all duration-200 ${
    isDragging ? "border-accent bg-accent/10" : "border-line/20 bg-raised hover:border-accent"
  } ${isUploading ? "opacity-50 pointer-events-none" : ""}`;

  const iconWrapperClassName = `p-4 rounded-full transition-colors ${
    isDragging ? "bg-accent/15" : "bg-raised"
  }`;

  const iconClassName = isDragging ? "text-accent" : "text-muted";

  const dropZoneText = isDragging ? "Drop your PDF here" : "Drag & drop your PDF here";

  return (
    <>
      {/* Overlay */}
      <div
        aria-label="Close upload modal"
        className={overlayClassName}
        onClick={isUploading ? undefined : onClose}
        onKeyDown={
          isUploading
            ? undefined
            : e => {
                if (e.key === "Escape") {
                  e.preventDefault();
                  onClose();
                }
              }
        }
      />

      {/* Modal */}
      <div className="ui-modal-viewport z-50" onClick={handleOverlayClick}>
        <div className="flex min-h-full items-start justify-center p-3 sm:items-center sm:p-4">
          <div
            data-testid="upload-modal-dialog"
            className="ui-modal-dialog flex w-full max-w-2xl flex-col rounded-2xl border border-line/20 bg-surface shadow-2xl transition-all duration-300"
            onClick={e => e.stopPropagation()}
          >
            {/* Header */}
            <div className="flex shrink-0 items-center justify-between border-b border-line/15 p-4 sm:p-6">
              <div className="flex items-center gap-3">
                <div className="rounded-lg bg-accent/15 p-2">
                  <Upload size={24} className="text-accent" />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-ink">Upload Document</h2>
                  <p className="text-sm text-muted">Add a PDF to your knowledge base</p>
                </div>
              </div>
              <button
                onClick={onClose}
                disabled={isUploading}
                className="rounded-lg p-2 text-muted transition-colors hover:bg-surface-hover disabled:cursor-not-allowed disabled:opacity-50"
              >
                <X size={24} />
              </button>
            </div>

            {/* Content */}
            <form
              data-testid="upload-modal-body"
              onSubmit={handleSubmit}
              className="min-h-0 space-y-6 overflow-y-auto overscroll-contain p-4 sm:p-6"
            >
              {/* Drag & Drop Zone - Using button for semantic HTML and accessibility */}
              {/* Drag events provide enhancement; accessible file input inside provides primary interaction */}
              <button
                type="button"
                onDragEnter={e => handleDragEvents(e, "enter")}
                onDragLeave={e => handleDragEvents(e, "leave")}
                onDragOver={e => handleDragEvents(e, "over")}
                onDrop={handleDrop}
                onClick={() => document.getElementById("file-input")?.click()}
                className={dropZoneClassName}
              >
                <div className="flex flex-col items-center justify-center gap-4 text-center">
                  <div className={iconWrapperClassName}>
                    <FileText size={48} className={iconClassName} />
                  </div>

                  <div>
                    <p className="mb-2 text-lg font-semibold text-ink">{dropZoneText}</p>
                    <p className="text-sm text-muted">or click to browse files</p>
                  </div>

                  <input
                    type="file"
                    id="file-input"
                    aria-label="Select PDF to upload"
                    accept=".pdf"
                    onChange={onFileChange}
                    disabled={isUploading}
                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer disabled:cursor-not-allowed"
                  />
                </div>
              </button>

              {/* Selected File */}
              {file && (
                <div className="flex items-center gap-3 rounded-lg border border-line/20 bg-raised p-4">
                  <FileText size={24} className="flex-shrink-0 text-accent" />
                  <div className="flex-1 min-w-0">
                    <p className="truncate text-sm font-medium text-ink">{file.name}</p>
                    <p className="text-xs text-muted">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                  </div>
                </div>
              )}

              {/* Language Selector */}
              <LanguageSelector
                selectedLanguage={selectedLanguage}
                onLanguageChange={onLanguageChange}
                disabled={isUploading}
              />

              {/* Upload Progress */}
              {isUploading && uploadProgress && (
                <UploadProgress
                  isUploading={isUploading}
                  progress={uploadProgress.progress}
                  status={uploadProgress.status}
                  message={uploadProgress.message}
                  estimatedTime={uploadProgress.estimatedTime}
                  chunksProcessed={uploadProgress.chunksProcessed}
                  totalChunks={uploadProgress.totalChunks}
                  currentPhase={uploadProgress.currentPhase}
                />
              )}

              {/* Alerts */}
              <AlertMessage alert={uploadAlert} />

              {/* Actions */}
              <div className="sticky bottom-0 -mx-4 flex items-center justify-end gap-3 border-t border-line/15 bg-surface px-4 pt-4 sm:-mx-6 sm:px-6">
                <button
                  type="button"
                  onClick={onClose}
                  disabled={isUploading}
                  className="ui-secondary-action rounded-lg px-4 py-2 text-sm font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={!file || isUploading}
                  className="ui-primary-action flex items-center gap-2 rounded-lg px-6 py-2 text-sm font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <Upload size={16} />
                  {isUploading ? "Uploading..." : "Upload Document"}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </>
  );
};
