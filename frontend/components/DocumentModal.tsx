"use client";

import { FormEvent, ChangeEvent, useState, useRef, useEffect } from "react";
import {
  Upload,
  X,
  FileText,
  Trash2,
  RefreshCw,
  BookOpen,
  AlertCircle,
} from "lucide-react";
import type { AlertState } from "@/lib/types";
import { AlertMessage } from "./AlertMessage";
import { useDocuments } from "@/hooks/useDocuments";
import { UploadProgress } from "./UploadProgress";
import { DocumentListSkeleton } from "./DocumentListSkeleton";
import { ConfirmModal } from "./ConfirmModal";

interface UploadProgressState {
  progress: number;
  status: "uploading" | "processing" | "complete" | "error";
  message?: string;
  estimatedTime?: string;
  chunksProcessed?: number;
  totalChunks?: number;
  currentPhase?: "upload" | "embedding";
}

interface DocumentModalProps {
  isOpen: boolean;
  onClose: () => void;
  file: File | null;
  isUploading: boolean;
  userId: string | null;
  uploadAlert: AlertState;
  statusAlert: AlertState | null;
  onFileChange: (e: ChangeEvent<HTMLInputElement>) => void;
  onUpload: (e: FormEvent) => void;
  uploadProgress?: UploadProgressState;
}

export const DocumentModal: React.FC<DocumentModalProps> = ({
  isOpen,
  onClose,
  file,
  isUploading,
  userId,
  uploadAlert,
  statusAlert,
  onFileChange,
  onUpload,
  uploadProgress,
}) => {
  const {
    documents,
    isLoading: isLoadingDocs,
    deleteDocument,
    refreshDocuments,
  } = useDocuments(userId);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const prevUploadingRef = useRef(isUploading);
  const [deletingDoc, setDeletingDoc] = useState<string | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<string | null>(
    null
  );
  const [dragActive, setDragActive] = useState(false);

  // Refresh documents when upload completes
  useEffect(() => {
    if (prevUploadingRef.current === true && isUploading === false) {
      setTimeout(() => {
        refreshDocuments();
      }, 500);
    }
    prevUploadingRef.current = isUploading;
  }, [isUploading, refreshDocuments]);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      if (droppedFile.type === "application/pdf") {
        // Crea un evento sintetico per il file change
        const dt = new DataTransfer();
        dt.items.add(droppedFile);
        if (fileInputRef.current) {
          fileInputRef.current.files = dt.files;
          const event = new Event("change", { bubbles: true });
          fileInputRef.current.dispatchEvent(event);
        }
      }
    }
  };

  const handleDelete = async (filename: string) => {
    setDeletingDoc(filename);
    try {
      await deleteDocument(filename);
      setShowDeleteConfirm(null);
    } catch (error) {
      console.error("Error deleting document:", error);
    } finally {
      setDeletingDoc(null);
    }
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return "N/A";
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString("it-IT", {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
      });
    } catch {
      return dateString;
    }
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Overlay */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
        onClick={onClose}
      >
        {/* Modal Content */}
        <div
          className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl w-full max-w-2xl transform transition-all duration-300"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="p-5 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white flex items-center space-x-2">
              <BookOpen size={24} className="text-blue-600" />
              <span>Document Management</span>
            </h2>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-800 dark:text-gray-400 dark:hover:text-white transition-colors"
            >
              <X size={24} />
            </button>
          </div>

          {/* Body */}
          <div className="p-5 space-y-6 max-h-[70vh] overflow-y-auto">
            {/* Upload Section */}
            <form onSubmit={onUpload} className="space-y-4">
              <div
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                className={`relative border-2 border-dashed rounded-lg p-8 text-center transition-all duration-300 cursor-pointer ${
                  dragActive
                    ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20"
                    : "border-gray-300 dark:border-gray-600 hover:border-blue-500 dark:hover:border-blue-500"
                }`}
              >
                <Upload
                  size={40}
                  className={`mx-auto mb-3 transition-colors ${
                    dragActive ? "text-blue-600" : "text-blue-500"
                  }`}
                />
                <p className="font-semibold text-gray-900 dark:text-white">
                  {dragActive
                    ? "Drop PDF here"
                    : "Drag & drop PDF or click to browse"}
                </p>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                  Document will be automatically indexed (max 10MB)
                </p>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf"
                  onChange={onFileChange}
                  className="hidden"
                  disabled={isUploading}
                />
                {file && (
                  <p className="mt-3 text-blue-600 dark:text-blue-400 font-medium">
                    Selected: <strong>{file.name}</strong>
                  </p>
                )}
              </div>

              <button
                type="submit"
                disabled={isUploading || !file || !userId}
                className={`w-full flex justify-center items-center py-3 px-4 text-sm font-bold rounded-lg shadow-lg transition duration-200 transform hover:scale-[1.01] ${
                  isUploading || !file || !userId
                    ? "bg-gray-300 text-gray-600 cursor-not-allowed dark:bg-gray-600 dark:text-gray-300"
                    : "bg-blue-600 text-white hover:bg-blue-700 hover:shadow-xl"
                }`}
              >
                {isUploading ? (
                  <>
                    <RefreshCw size={18} className="animate-spin mr-2" />
                    Upload & Indexing in Progress...
                  </>
                ) : (
                  <>
                    <Upload size={18} className="mr-2" />
                    Upload & Index Document
                  </>
                )}
              </button>

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
              <div className="space-y-2">
                {statusAlert && <AlertMessage alert={statusAlert} />}
                <AlertMessage alert={uploadAlert} />
              </div>
            </form>

            {/* Indexed Documents Section */}
            <div>
              <div className="flex items-center justify-between mb-3 border-b pb-2 border-gray-200 dark:border-gray-700">
                <h3 className="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
                  <FileText size={18} className="text-blue-600" />
                  Indexed Documents ({documents.length})
                </h3>
                <button
                  onClick={refreshDocuments}
                  title="Refresh list"
                  className="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                  disabled={isLoadingDocs}
                >
                  <RefreshCw
                    size={16}
                    className={`text-gray-600 dark:text-gray-400 ${
                      isLoadingDocs ? "animate-spin" : ""
                    }`}
                  />
                </button>
              </div>

              <div className="space-y-3 max-h-60 overflow-y-auto pr-2">
                {isLoadingDocs ? (
                  <DocumentListSkeleton count={3} />
                ) : documents.length === 0 ? (
                  <div className="text-center py-8 px-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                    <AlertCircle
                      size={40}
                      className="mx-auto text-gray-400 mb-3"
                    />
                    <p className="text-gray-500 dark:text-gray-400 italic">
                      No documents uploaded yet.
                    </p>
                    <p className="text-sm text-gray-400 dark:text-gray-500 mt-1">
                      Upload a PDF to start asking questions.
                    </p>
                  </div>
                ) : (
                  documents.map((doc) => (
                    <div
                      key={doc.filename}
                      className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg shadow-sm hover:shadow-md transition border border-gray-200 dark:border-gray-600"
                    >
                      <div className="flex items-center space-x-3 min-w-0 flex-1">
                        <FileText
                          size={20}
                          className="text-blue-600 flex-shrink-0"
                        />
                        <div className="min-w-0 flex-1">
                          <p
                            className="font-semibold truncate text-gray-900 dark:text-white text-sm"
                            title={doc.filename}
                          >
                            {doc.filename}
                          </p>
                          <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                            <span>
                              {doc.chunks_count?.toLocaleString() || "0"} chunks
                            </span>
                            {doc.language && doc.language !== "unknown" && (
                              <>
                                <span>•</span>
                                <span className="uppercase">{doc.language}</span>
                              </>
                            )}
                            {doc.uploaded_at && (
                              <>
                                <span>•</span>
                                <span>{formatDate(doc.uploaded_at)}</span>
                              </>
                            )}
                          </div>
                        </div>
                      </div>
                      <button
                        onClick={() => setShowDeleteConfirm(doc.filename)}
                        disabled={deletingDoc === doc.filename}
                        title="Delete document"
                        className="ml-3 p-2 rounded-full text-red-600 hover:bg-red-100 dark:hover:bg-red-900/30 transition-colors flex-shrink-0 disabled:opacity-50"
                      >
                        {deletingDoc === doc.filename ? (
                          <RefreshCw size={16} className="animate-spin" />
                        ) : (
                          <Trash2 size={16} />
                        )}
                      </button>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Delete Confirmation Modal */}
      <ConfirmModal
        isOpen={!!showDeleteConfirm}
        title={`Delete "${showDeleteConfirm}"?`}
        message="This action cannot be undone. All embeddings and chunks will be permanently removed."
        confirmText="Delete"
        cancelText="Cancel"
        variant="danger"
        onConfirm={() => showDeleteConfirm && handleDelete(showDeleteConfirm)}
        onCancel={() => setShowDeleteConfirm(null)}
      />
    </>
  );
};
