"use client";

import { FormEvent, ChangeEvent, useRef, useEffect } from "react";
import { Upload, X, FileText, Trash2, RefreshCw, BookOpen, AlertCircle } from "lucide-react";
import type { AlertState } from "@/lib/types";
import { AlertMessage } from "./AlertMessage";
import { useDocuments } from "@/hooks/useDocuments";
import { UploadProgress } from "./UploadProgress";
import { DocumentListSkeleton } from "./DocumentListSkeleton";
import { ConfirmModal } from "./ConfirmModal";
import { useDragAndDrop } from "./DocumentModal/useDragAndDrop";
import { useDocumentDeletion } from "./DocumentModal/useDocumentDeletion";
import { formatDate } from "./DocumentModal/documentHelpers";
import { IndexedDocumentsList } from "./DocumentModal/IndexedDocumentsList";
import { EmptyDocumentsState } from "./DocumentModal/EmptyDocumentsState";
import { DocumentUploadSection } from "./DocumentModal/DocumentUploadSection";

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

  // Use custom hooks for drag-and-drop and deletion
  const { dragActive, handleDrag, handleDrop } = useDragAndDrop({
    fileInputRef,
  });
  const { deletingDoc, showDeleteConfirm, handleDelete, openDeleteConfirm, closeDeleteConfirm } =
    useDocumentDeletion({ deleteDocument });

  // Refresh documents when upload completes
  useEffect(() => {
    if (prevUploadingRef.current === true && isUploading === false) {
      setTimeout(() => {
        refreshDocuments();
      }, 500);
    }
    prevUploadingRef.current = isUploading;
  }, [isUploading, refreshDocuments]);

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
          onClick={e => e.stopPropagation()}
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
            <DocumentUploadSection
              file={file}
              isUploading={isUploading}
              userId={userId}
              dragActive={dragActive}
              uploadAlert={uploadAlert}
              statusAlert={statusAlert}
              uploadProgress={uploadProgress}
              fileInputRef={fileInputRef}
              onFileChange={onFileChange}
              onUpload={onUpload}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
            />

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
                  <EmptyDocumentsState />
                ) : (
                  <IndexedDocumentsList
                    documents={documents}
                    deletingDoc={deletingDoc}
                    onDeleteClick={openDeleteConfirm}
                  />
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
        onCancel={closeDeleteConfirm}
      />
    </>
  );
};
