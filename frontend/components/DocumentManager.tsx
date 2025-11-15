"use client";

import { FormEvent, ChangeEvent, useState, useRef, useEffect } from "react";
import {
  Upload,
  Loader,
  FileText,
  Trash2,
  AlertCircle,
  RefreshCw,
} from "lucide-react";
import type { AlertState } from "@/lib/types";
import { AlertMessage } from "./AlertMessage";
import { useDocuments } from "@/hooks/useDocuments";
import { useUploadProgress } from "@/hooks/useUploadProgress";
import { UploadProgress } from "./UploadProgress";
import { DocumentListSkeleton } from "./DocumentListSkeleton";
interface DocumentManagerProps {
  file: File | null;
  isUploading: boolean;
  userId: string | null;
  uploadAlert: AlertState;
  statusAlert: AlertState | null;
  onFileChange: (e: ChangeEvent<HTMLInputElement>) => void;
  onUpload: (e: FormEvent) => void;
}

export const DocumentManager: React.FC<DocumentManagerProps> = ({
  file,
  isUploading,
  userId,
  uploadAlert,
  statusAlert,
  onFileChange,
  onUpload,
}) => {
  const {
    documents,
    isLoading: isLoadingDocs,
    deleteDocument,
    refreshDocuments,
  } = useDocuments(userId);

  // Track previous uploading state to detect completion
  const prevUploadingRef = useRef(isUploading);

  // Estimate upload time based on file size (if available)
  const estimatedTime = file
    ? Math.max(60, Math.min(300, (file.size / (1024 * 1024)) * 30))
    : 180;

  // Track upload progress
  const progressState = useUploadProgress({
    isUploading,
    estimatedTotalTime: estimatedTime,
  });

  // Refresh documents when upload completes
  useEffect(() => {
    if (prevUploadingRef.current === true && isUploading === false) {
      console.log("🔄 Upload completed, refreshing document list...");
      console.log("📊 Current documents before refresh:", documents.length);
      // Small delay to ensure backend has processed everything
      setTimeout(() => {
        console.log("⏰ Executing delayed refresh...");
        refreshDocuments();
      }, 500);
    }
    prevUploadingRef.current = isUploading;
  }, [isUploading, refreshDocuments]);

  // Log when documents change
  useEffect(() => {
    console.log(
      "📝 Documents state changed:",
      documents.length,
      documents.map((d) => d.filename)
    );
  }, [documents]);

  console.log(
    "📋 DocumentManager render - documents:",
    documents?.length || 0,
    documents
  );

  const [deletingDoc, setDeletingDoc] = useState<string | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<string | null>(
    null
  );

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

  return (
    <section className="space-y-4">
      {/* Upload Area */}
      <div>
        <h2 className="text-lg font-bold text-gray-800 dark:text-white mb-3 flex items-center border-b border-gray-100 dark:border-gray-700 pb-2">
          <Upload size={16} className="mr-2 text-blue-600" /> Documents
        </h2>

        <form onSubmit={onUpload} className="space-y-4">
          {/* Drag & Drop Upload Area */}
          <div className="relative border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-6 hover:border-blue-400 dark:hover:border-blue-500 transition duration-300 cursor-pointer bg-gray-50 dark:bg-gray-900/30">
            <input
              type="file"
              id="pdf-upload"
              accept=".pdf"
              onChange={onFileChange}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              disabled={isUploading || !userId}
            />
            <div className="text-center pointer-events-none">
              <Upload size={32} className="mx-auto text-blue-500 mb-3" />
              {file ? (
                <>
                  <p className="text-sm font-semibold text-blue-600 dark:text-blue-400 truncate">
                    {file.name}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    Ready to upload and index
                  </p>
                </>
              ) : (
                <>
                  <p className="text-sm text-gray-600 dark:text-gray-300 font-medium">
                    Drop PDF here or click to browse
                  </p>
                  <p className="text-xs text-gray-400 mt-1">
                    Document will be automatically indexed after upload
                  </p>
                </>
              )}
            </div>
          </div>

          {/* Upload Button */}
          <button
            type="submit"
            disabled={!file || isUploading || !userId}
            className="w-full py-2.5 px-4 rounded-lg font-medium text-sm transition-all duration-300 flex items-center justify-center gap-2
              bg-gradient-to-r from-blue-600 to-purple-600 text-white
              hover:from-blue-700 hover:to-purple-700 
              disabled:from-gray-400 disabled:to-gray-500 disabled:cursor-not-allowed
              shadow-lg hover:shadow-xl disabled:shadow-none"
          >
            {isUploading ? (
              <>
                <Loader className="animate-spin" size={16} />
                Uploading & Indexing...
              </>
            ) : (
              <>
                <Upload size={16} />
                Upload & Index Document
              </>
            )}
          </button>

          {/* Upload Progress Bar */}
          {isUploading && (
            <UploadProgress
              isUploading={isUploading}
              progress={progressState.progress}
              status={progressState.status}
              message={progressState.message}
              estimatedTime={progressState.estimatedTime}
              chunksProcessed={progressState.chunksProcessed}
              totalChunks={progressState.totalChunks}
            />
          )}

          {/* Alerts */}
          <div className="space-y-2">
            {statusAlert && <AlertMessage alert={statusAlert} />}
            <AlertMessage alert={uploadAlert} />
          </div>
        </form>
      </div>

      {/* Document List */}
      <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 flex items-center gap-2">
            <FileText size={14} />
            Indexed Documents ({documents.length})
          </h3>
          <button
            onClick={refreshDocuments}
            disabled={isLoadingDocs}
            className="p-1.5 text-gray-500 hover:text-blue-600 dark:text-gray-400 dark:hover:text-blue-400 transition disabled:opacity-50"
            title="Refresh list"
          >
            <RefreshCw
              size={14}
              className={isLoadingDocs ? "animate-spin" : ""}
            />
          </button>
        </div>

        {isLoadingDocs && documents.length === 0 ? (
          // Show skeleton only on initial load (no documents yet)
          <DocumentListSkeleton />
        ) : documents.length === 0 ? (
          // Show empty state when not loading and no documents
          <div className="text-center py-6 bg-gray-50 dark:bg-gray-900/30 rounded-lg border border-dashed border-gray-300 dark:border-gray-700">
            <FileText
              size={32}
              className="mx-auto mb-2 text-gray-300 dark:text-gray-600"
            />
            <p className="text-xs text-gray-500 dark:text-gray-400">
              No documents uploaded yet
            </p>
          </div>
        ) : (
          <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
            {documents.map((doc) => (
              <div
                key={doc.filename}
                className="group relative bg-gray-50 dark:bg-gray-900/50 border border-gray-200 dark:border-gray-700 rounded-lg p-3 hover:shadow-md hover:border-blue-300 dark:hover:border-blue-700 transition-all"
              >
                {/* Delete Confirmation Overlay */}
                {showDeleteConfirm === doc.filename && (
                  <div className="absolute inset-0 bg-white/98 dark:bg-gray-900/98 rounded-lg flex items-center justify-center z-10 backdrop-blur-sm">
                    <div className="text-center px-4">
                      <AlertCircle
                        size={24}
                        className="mx-auto mb-2 text-red-600"
                      />
                      <p className="text-xs font-semibold text-gray-800 dark:text-white mb-3">
                        Delete &quot;{doc.filename}&quot;?
                      </p>
                      <div className="flex gap-2 justify-center">
                        <button
                          onClick={() => handleDelete(doc.filename)}
                          disabled={deletingDoc === doc.filename}
                          className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-xs font-medium rounded-lg transition disabled:opacity-50 flex items-center gap-1"
                        >
                          {deletingDoc === doc.filename ? (
                            <Loader className="animate-spin" size={12} />
                          ) : (
                            <Trash2 size={12} />
                          )}
                          Delete
                        </button>
                        <button
                          onClick={() => setShowDeleteConfirm(null)}
                          className="px-4 py-2 bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-800 dark:text-white text-xs font-medium rounded-lg transition"
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  </div>
                )}

                {/* Document Info */}
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0 w-9 h-9 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center shadow-sm">
                    <FileText size={18} className="text-white" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold text-gray-800 dark:text-white truncate mb-1">
                      {doc.filename}
                    </p>
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="inline-flex items-center gap-1 text-xs text-gray-600 dark:text-gray-400 bg-gray-200 dark:bg-gray-800 px-2 py-0.5 rounded-full">
                        <span className="font-medium">{doc.chunks_count}</span>{" "}
                        chunks
                      </span>
                      {doc.language && doc.language !== "unknown" && (
                        <span className="inline-flex items-center text-xs text-gray-600 dark:text-gray-400 bg-gray-200 dark:bg-gray-800 px-2 py-0.5 rounded-full uppercase font-medium">
                          {doc.language}
                        </span>
                      )}
                    </div>
                  </div>
                  <button
                    onClick={() => setShowDeleteConfirm(doc.filename)}
                    disabled={deletingDoc === doc.filename}
                    className="flex-shrink-0 p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition opacity-0 group-hover:opacity-100 disabled:opacity-50"
                    title="Delete document"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
};
