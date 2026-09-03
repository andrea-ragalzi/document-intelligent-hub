"use client";

import { X, Upload, FileText } from "lucide-react";
import { FormEvent, ChangeEvent, useState, DragEvent, useEffect } from "react";
import { UploadProgress } from "./UploadProgress";
import { AlertMessage } from "./AlertMessage";
import { LanguageSelector } from "./LanguageSelector";
import type { AlertState } from "@/lib/types";
import type { DuplicateAction } from "@/hooks/useDocumentUpload";

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
  files: File[];
  isUploading: boolean;
  uploadAlert: AlertState;
  pendingDuplicate: File | null;
  onFileChange: (e: ChangeEvent<HTMLInputElement>) => void;
  onUpload: (e: FormEvent) => void;
  onResolveDuplicate: (action: DuplicateAction) => void;
  uploadProgress?: UploadProgressState;
  selectedLanguage: string;
  onLanguageChange: (lang: string) => void;
}

const SelectedFiles: React.FC<{ files: File[] }> = ({ files }) => {
  if (!files.length) return null;

  return (
    <div className="flex items-center gap-3 rounded-lg border border-line/20 bg-raised p-4">
      <FileText size={24} className="flex-shrink-0 text-accent" />
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-ink">
          {files.length} PDF{files.length === 1 ? "" : "s"} selected
        </p>
        <ul className="mt-1 max-h-24 space-y-1 overflow-y-auto text-xs text-muted">
          {files.map((file, index) => (
            <li key={`${file.name}-${file.lastModified}-${index}`} className="truncate">
              {file.name} · {(file.size / 1024 / 1024).toFixed(2)} MB
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};

interface DuplicateFileOptionsProps {
  file: File | null;
  onResolve: (action: DuplicateAction) => void;
}

const DuplicateFileOptions: React.FC<DuplicateFileOptionsProps> = ({ file, onResolve }) => {
  if (!file) return null;

  return (
    <section
      aria-label="Duplicate file options"
      className="rounded-lg border border-line/20 bg-raised p-4"
    >
      <h3 className="text-sm font-semibold text-ink">A document already has this name</h3>
      <p className="mt-1 break-words text-sm text-muted">{file.name}</p>
      <div className="mt-3 flex flex-wrap gap-2">
        <button
          type="button"
          onClick={() => onResolve("replace")}
          className="ui-primary-action rounded-lg px-3 py-2 text-sm font-medium"
        >
          Replace
        </button>
        <button
          type="button"
          onClick={() => onResolve("rename")}
          className="ui-secondary-action rounded-lg px-3 py-2 text-sm font-medium"
        >
          Rename copy
        </button>
        <button
          type="button"
          onClick={() => onResolve("skip")}
          className="ui-secondary-action rounded-lg px-3 py-2 text-sm font-medium"
        >
          Skip
        </button>
      </div>
    </section>
  );
};

const getUploadButtonLabel = (fileCount: number, isUploading: boolean): string => {
  if (isUploading) return "Uploading...";
  if (fileCount === 1) return "Upload Document";
  return `Upload ${fileCount} Documents`;
};

export const UploadModal: React.FC<UploadModalProps> = ({
  isOpen,
  onClose,
  files,
  isUploading,
  uploadAlert,
  pendingDuplicate,
  onFileChange,
  onUpload,
  onResolveDuplicate,
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

  const dropZoneText = isDragging ? "Drop your PDFs here" : "Drag & drop your PDFs here";

  return (
    <>
      {/* Overlay */}
      <button
        type="button"
        aria-label="Close upload modal"
        className={`${overlayClassName} border-0 p-0`}
        onClick={onClose}
        disabled={isUploading}
      />

      {/* Modal */}
      <div className="ui-modal-viewport z-50 pointer-events-none">
        <div className="flex min-h-full items-start justify-center p-3 sm:items-center sm:p-4">
          <div
            data-testid="upload-modal-dialog"
            className="ui-modal-dialog pointer-events-auto flex w-full max-w-2xl flex-col rounded-2xl border border-line/20 bg-surface shadow-2xl transition-all duration-300"
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
                    multiple
                    onChange={onFileChange}
                    disabled={isUploading}
                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer disabled:cursor-not-allowed"
                  />
                </div>
              </button>

              <SelectedFiles files={files} />
              <DuplicateFileOptions file={pendingDuplicate} onResolve={onResolveDuplicate} />

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
                  disabled={!files.length || isUploading || !!pendingDuplicate}
                  className="ui-primary-action flex items-center gap-2 rounded-lg px-6 py-2 text-sm font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <Upload size={16} />
                  {getUploadButtonLabel(files.length, isUploading)}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </>
  );
};
