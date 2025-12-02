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

  const overlayClassName = `fixed inset-0 bg-black/50 dark:bg-indigo-950/80 z-50 transition-opacity duration-300 ${
    isUploading ? "cursor-not-allowed" : "cursor-pointer"
  }`;

  const dropZoneClassName = `relative border-2 border-dashed rounded-xl p-8 transition-all duration-200 ${
    isDragging
      ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20"
      : "border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-900/50"
  } ${isUploading ? "opacity-50 pointer-events-none" : ""}`;

  const iconWrapperClassName = `p-4 rounded-full transition-colors ${
    isDragging ? "bg-blue-100 dark:bg-blue-900/40" : "bg-gray-200 dark:bg-gray-700"
  }`;

  const iconClassName = isDragging
    ? "text-blue-600 dark:text-blue-400"
    : "text-gray-400 dark:text-gray-500";

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
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 pointer-events-none">
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-2xl pointer-events-auto transform transition-all duration-300">
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-blue-100 dark:bg-blue-900/30">
                <Upload size={24} className="text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-gray-900 dark:text-white">Upload Document</h2>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Add a PDF to your knowledge base
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              disabled={isUploading}
              className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <X size={24} className="text-gray-500 dark:text-gray-400" />
            </button>
          </div>

          {/* Content */}
          <form onSubmit={handleSubmit} className="p-6 space-y-6">
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
                  <p className="text-lg font-semibold text-gray-700 dark:text-gray-300 mb-2">
                    {dropZoneText}
                  </p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    or click to browse files
                  </p>
                </div>

                <input
                  type="file"
                  id="file-input"
                  accept=".pdf"
                  onChange={onFileChange}
                  disabled={isUploading}
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer disabled:cursor-not-allowed"
                />
              </div>
            </button>

            {/* Selected File */}
            {file && (
              <div className="flex items-center gap-3 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                <FileText size={24} className="text-blue-600 dark:text-blue-400 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                    {file.name}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    {(file.size / 1024 / 1024).toFixed(2)} MB
                  </p>
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
            <div className="flex items-center justify-end gap-3 pt-4 border-t border-gray-200 dark:border-gray-700">
              <button
                type="button"
                onClick={onClose}
                disabled={isUploading}
                className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={!file || isUploading}
                className="px-6 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                <Upload size={16} />
                {isUploading ? "Uploading..." : "Upload Document"}
              </button>
            </div>
          </form>
        </div>
      </div>
    </>
  );
};
