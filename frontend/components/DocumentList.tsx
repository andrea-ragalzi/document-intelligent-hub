"use client";

import { FileText, Trash2, Loader, AlertCircle } from "lucide-react";
import { useState } from "react";

export interface Document {
  filename: string;
  chunks_count: number;
  language?: string;
  uploaded_at?: string;
}

interface DocumentListProps {
  documents: Document[];
  isLoading: boolean;
  onDeleteDocument: (filename: string) => void;
  onRefresh: () => void;
}

export const DocumentList: React.FC<DocumentListProps> = ({
  documents,
  isLoading,
  onDeleteDocument,
  onRefresh,
}) => {
  const [deletingDoc, setDeletingDoc] = useState<string | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<string | null>(
    null
  );

  const handleDelete = async (filename: string) => {
    setDeletingDoc(filename);
    try {
      await onDeleteDocument(filename);
      setShowDeleteConfirm(null);
      onRefresh();
    } catch (error) {
      console.error("Error deleting document:", error);
    } finally {
      setDeletingDoc(null);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader className="animate-spin text-blue-600" size={24} />
        <span className="ml-2 text-sm text-gray-500 dark:text-gray-400">
          Loading documents...
        </span>
      </div>
    );
  }

  if (documents.length === 0) {
    return (
      <div className="text-center py-8">
        <FileText
          size={40}
          className="mx-auto mb-3 text-gray-300 dark:text-gray-600"
        />
        <p className="text-sm text-gray-500 dark:text-gray-400">
          No documents uploaded yet
        </p>
        <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
          Upload a PDF to get started
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300">
          Indexed Documents ({documents.length})
        </h3>
      </div>

      <div className="space-y-2 max-h-64 overflow-y-auto">
        {documents.map((doc) => (
          <div
            key={doc.filename}
            className="group relative bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-3 hover:shadow-md transition-all"
          >
            {/* Delete Confirmation Overlay */}
            {showDeleteConfirm === doc.filename && (
              <div className="absolute inset-0 bg-white/95 dark:bg-gray-800/95 rounded-lg flex items-center justify-center z-10 backdrop-blur-sm">
                <div className="text-center px-4">
                  <AlertCircle
                    size={20}
                    className="mx-auto mb-2 text-red-600"
                  />
                  <p className="text-xs font-semibold text-gray-800 dark:text-white mb-3">
                    Delete this document?
                  </p>
                  <div className="flex gap-2 justify-center">
                    <button
                      onClick={() => handleDelete(doc.filename)}
                      disabled={deletingDoc === doc.filename}
                      className="px-3 py-1.5 bg-red-600 hover:bg-red-700 text-white text-xs font-medium rounded transition disabled:opacity-50"
                    >
                      {deletingDoc === doc.filename ? (
                        <Loader className="animate-spin" size={12} />
                      ) : (
                        "Delete"
                      )}
                    </button>
                    <button
                      onClick={() => setShowDeleteConfirm(null)}
                      className="px-3 py-1.5 bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-800 dark:text-white text-xs font-medium rounded transition"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* Document Info */}
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0 w-8 h-8 bg-blue-100 dark:bg-blue-900/30 rounded flex items-center justify-center">
                <FileText size={16} className="text-blue-600" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-800 dark:text-white truncate">
                  {doc.filename}
                </p>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-xs text-gray-500 dark:text-gray-400">
                    {doc.chunks_count} chunks
                  </span>
                  {doc.language && doc.language !== "unknown" && (
                    <>
                      <span className="text-xs text-gray-400">•</span>
                      <span className="text-xs text-gray-500 dark:text-gray-400 uppercase">
                        {doc.language}
                      </span>
                    </>
                  )}
                </div>
              </div>
              <button
                onClick={() => setShowDeleteConfirm(doc.filename)}
                disabled={deletingDoc === doc.filename}
                className="flex-shrink-0 p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded transition opacity-0 group-hover:opacity-100 disabled:opacity-50"
                title="Delete document"
              >
                <Trash2 size={14} />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
