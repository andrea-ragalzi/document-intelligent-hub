"use client";

import {
  FileText,
  Trash2,
  Loader,
  AlertCircle,
  Square,
  CheckSquare,
} from "lucide-react";
import React, { useState } from "react";

export interface Document {
  filename: string;
  chunks_count: number;
  language?: string;
}

interface DocumentListProps {
  documents: Document[];
  deletingDoc: string | null;
  onDelete: (filename: string) => void;
}

const DocumentList: React.FC<DocumentListProps> = ({
  documents,
  deletingDoc,
  onDelete,
}) => {
  const [selectedDocs, setSelectedDocs] = useState<string[]>([]);

  const handleSelect = (filename: string) => {
    setSelectedDocs((prev) =>
      prev.includes(filename)
        ? prev.filter((f) => f !== filename)
        : [...prev, filename]
    );
  };

  const handleSelectAll = () => {
    if (selectedDocs.length === documents.length) {
      setSelectedDocs([]);
    } else {
      setSelectedDocs(documents.map((d) => d.filename));
    }
  };

  const handleDeleteSelected = () => {
    if (selectedDocs.length === 0) return;
    setDeleteMultipleModalOpen(true);
  };

  const confirmDeleteSelected = () => {
    // Delete all selected documents
    selectedDocs.forEach((filename) => {
      onDelete(filename);
    });
    // Reset selection
    setSelectedDocs([]);
    setDeleteMultipleModalOpen(false);
  };

  const [modalOpen, setModalOpen] = useState(false);
  const [deleteMultipleModalOpen, setDeleteMultipleModalOpen] = useState(false);
  const [pendingDelete, setPendingDelete] = useState<Document | null>(null);

  const openDeleteModal = (doc: Document) => {
    setPendingDelete(doc);
    setModalOpen(true);
  };

  const closeDeleteModal = () => {
    setModalOpen(false);
    setPendingDelete(null);
  };

  const handleDelete = (filename: string) => {
    onDelete(filename);
    closeDeleteModal();
  };

  return (
    <>
      <div className="flex items-center justify-between gap-2 mb-3 px-1">
        <button
          onClick={handleSelectAll}
          className="flex items-center gap-2 hover:opacity-70 transition"
        >
          {selectedDocs.length === documents.length && documents.length > 0 ? (
            <CheckSquare size={16} className="text-blue-600" />
          ) : (
            <Square size={16} className="text-gray-400" />
          )}
          <span className="text-xs text-gray-700 dark:text-gray-200 select-none">
            Select all
          </span>
        </button>
        {selectedDocs.length > 0 && (
          <button
            onClick={handleDeleteSelected}
            className="px-3 py-1.5 bg-red-600 hover:bg-red-700 text-white text-xs font-medium rounded transition"
          >
            Delete selected ({selectedDocs.length})
          </button>
        )}
      </div>
      <div className="space-y-2">
        <div className="space-y-2 max-h-64 overflow-y-auto">
          {documents.map((doc) => (
            <div
              key={doc.filename}
              className="group relative bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-3 hover:shadow-md transition-all"
            >
              <div className="flex items-center gap-3">
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
                  onClick={() => handleSelect(doc.filename)}
                  className="flex-shrink-0 p-1 hover:opacity-70 transition"
                  title="Seleziona documento"
                >
                  {selectedDocs.includes(doc.filename) ? (
                    <CheckSquare size={16} className="text-blue-600" />
                  ) : (
                    <Square size={16} className="text-gray-400" />
                  )}
                </button>
                <button
                  onClick={() => openDeleteModal(doc)}
                  disabled={deletingDoc === doc.filename}
                  className="flex-shrink-0 p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded transition disabled:opacity-50"
                  title="Delete document"
                >
                  <Trash2 size={16} />
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
      {/* Delete Confirmation Modal */}
      {modalOpen && pendingDelete && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl p-6 w-full max-w-xs mx-2">
            <div className="flex flex-col items-center text-center">
              <AlertCircle size={32} className="mb-2 text-red-600" />
              <p className="text-base font-semibold text-gray-800 dark:text-white mb-2">
                Delete document?
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400 mb-4 break-all">
                {pendingDelete.filename}
              </p>
              <div className="flex gap-2 w-full justify-center">
                <button
                  onClick={() => handleDelete(pendingDelete.filename)}
                  disabled={deletingDoc === pendingDelete.filename}
                  className="flex-1 px-3 py-2 bg-red-600 hover:bg-red-700 text-white text-xs font-medium rounded transition disabled:opacity-50"
                >
                  {deletingDoc === pendingDelete.filename ? (
                    <Loader className="animate-spin" size={14} />
                  ) : (
                    "Delete"
                  )}
                </button>
                <button
                  onClick={closeDeleteModal}
                  disabled={deletingDoc === pendingDelete.filename}
                  className="flex-1 px-3 py-2 bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-800 dark:text-white text-xs font-medium rounded transition"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
      {/* Delete Multiple Confirmation Modal */}
      {deleteMultipleModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl p-6 w-full max-w-md mx-2">
            <div className="flex flex-col items-center text-center">
              <AlertCircle size={32} className="mb-3 text-red-600" />
              <p className="text-base font-semibold text-gray-800 dark:text-white mb-2">
                Delete {selectedDocs.length} document
                {selectedDocs.length > 1 ? "s" : ""}?
              </p>
              <div className="w-full max-h-48 overflow-y-auto mb-4 bg-gray-50 dark:bg-gray-900/50 rounded-lg p-3">
                <ul className="text-left">
                  {selectedDocs.map((filename) => (
                    <li
                      key={filename}
                      className="text-xs text-gray-700 dark:text-gray-300 break-all py-1.5 border-b border-gray-200 dark:border-gray-700 last:border-0"
                    >
                      • {filename}
                    </li>
                  ))}
                </ul>
              </div>
              <p className="text-xs text-gray-500 dark:text-gray-400 mb-4">
                This action cannot be undone.
              </p>
              <div className="flex gap-2 w-full justify-center">
                <button
                  onClick={confirmDeleteSelected}
                  className="flex-1 px-3 py-2 bg-red-600 hover:bg-red-700 text-white text-xs font-medium rounded transition"
                >
                  Delete
                </button>
                <button
                  onClick={() => setDeleteMultipleModalOpen(false)}
                  className="flex-1 px-3 py-2 bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-800 dark:text-white text-xs font-medium rounded transition"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default DocumentList;
