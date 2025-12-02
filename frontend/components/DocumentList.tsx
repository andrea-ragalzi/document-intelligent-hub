"use client";

import { FileText, Trash2, Loader, AlertCircle, MoreVertical, CheckCircle } from "lucide-react";
import React, { useState } from "react";
import { useDocumentMenu } from "./DocumentList/useDocumentMenu";
import { useDocumentSelection } from "./DocumentList/useDocumentSelection";
import { DocumentItem } from "./DocumentList/DocumentItem";
import { DocumentContextMenu } from "./DocumentList/DocumentContextMenu";

export interface Document {
  filename: string;
  chunks_count: number;
  language?: string;
}

interface DocumentListProps {
  documents: Document[] | undefined;
  deletingDoc: string | null;
  onDelete: (filename: string) => void;
  isServerOnline?: boolean;
}

const DocumentList: React.FC<DocumentListProps> = ({
  documents,
  deletingDoc,
  onDelete,
  isServerOnline = true,
}) => {
  // Safety check: ensure documents is always an array
  const safeDocuments = documents || [];

  // Use custom hooks for selection and menu management
  const {
    selectedDocs,
    isSelectionMode,
    deleteMultipleModalOpen,
    handleSelect,
    handleSelectAll,
    handleDeleteSelected,
    confirmDeleteSelected,
    closeDeleteMultipleModal,
  } = useDocumentSelection({ documents: safeDocuments });

  const {
    openKebabId,
    menuPosition,
    kebabRef,
    menuRef,
    dragY,
    isDragging,
    closeContextMenu,
    runActionAndCloseMenu,
    handleTouchStart,
    handleTouchEnd,
    handleDragStart,
    handleDragMove,
    handleDragEnd,
    setOpenKebabId,
    setMenuPosition,
  } = useDocumentMenu({ isSelectionMode });

  // Sort documents by name (alphabetically)
  const sortedDocuments = [...safeDocuments].sort((a, b) => a.filename.localeCompare(b.filename));

  const [modalOpen, setModalOpen] = useState(false);
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
      {/* Bulk Action Bar - Automatically appears when there are selections */}
      {isSelectionMode && (
        <div className="sticky top-0 z-10 bg-indigo-100 dark:bg-indigo-900/50 border-2 border-indigo-300 dark:border-indigo-600 rounded-lg mb-3 p-3 shadow-md">
          <div className="flex items-center justify-between gap-2">
            <button
              onClick={handleSelectAll}
              className="text-sm text-indigo-700 dark:text-indigo-300 hover:text-indigo-900 dark:hover:text-indigo-100 transition font-semibold"
            >
              {selectedDocs.length === safeDocuments.length && safeDocuments.length > 0
                ? "Deselect All"
                : "Select All"}
            </button>
            <button
              onClick={handleDeleteSelected}
              disabled={isServerOnline === false}
              className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-sm font-semibold rounded-lg transition-all duration-200 shadow-sm hover:shadow-md flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
              title={
                isServerOnline === false
                  ? "Server offline - delete unavailable"
                  : "Delete selected documents"
              }
            >
              <Trash2 size={16} />
              <span>Delete ({selectedDocs.length})</span>
            </button>
          </div>
        </div>
      )}

      <div className="space-y-2 flex-1 flex flex-col overflow-hidden">
        <div className="space-y-2 flex-1 overflow-y-auto">
          {sortedDocuments.length === 0 ? (
            <div className="text-center py-8 text-gray-500 dark:text-gray-400 text-sm">
              No documents uploaded yet
            </div>
          ) : (
            sortedDocuments.map(doc => {
              const isSelected = selectedDocs.includes(doc.filename);
              const isKebabOpen = openKebabId === doc.filename;

              return (
                <DocumentItem
                  key={doc.filename}
                  doc={doc}
                  isSelected={isSelected}
                  isSelectionMode={isSelectionMode}
                  isKebabOpen={isKebabOpen}
                  onSelect={handleSelect}
                  onTouchStart={handleTouchStart}
                  onTouchEnd={handleTouchEnd}
                  onContextMenu={(e, rect) => {
                    setMenuPosition({
                      top: rect.bottom + window.scrollY + 8,
                      right: window.innerWidth - rect.right + window.scrollX,
                    });
                    setOpenKebabId(doc.filename);
                  }}
                  onKebabClick={(e, rect) => {
                    setMenuPosition({
                      top: rect.bottom + window.scrollY + 4,
                      right: window.innerWidth - rect.right + window.scrollX,
                    });
                    setOpenKebabId(doc.filename);
                  }}
                  onCloseKebab={closeContextMenu}
                  kebabRef={(el, filename) => {
                    kebabRef.current[filename] = el;
                  }}
                />
              );
            })
          )}
        </div>
      </div>

      {/* Dropdown Menu - Rendered at root level to avoid z-index issues */}
      <DocumentContextMenu
        isOpen={!!openKebabId}
        menuPosition={menuPosition}
        dragY={dragY}
        isDragging={isDragging}
        selectedDoc={openKebabId}
        isServerOnline={isServerOnline}
        menuRef={menuRef}
        onClose={closeContextMenu}
        onDelete={filename => {
          const doc = safeDocuments.find(d => d.filename === filename);
          if (doc) openDeleteModal(doc);
        }}
        onDragStart={handleDragStart}
        onDragMove={handleDragMove}
        onDragEnd={handleDragEnd}
        runActionAndCloseMenu={runActionAndCloseMenu}
      />

      {/* Delete Confirmation Modal */}
      {modalOpen && pendingDelete && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 dark:bg-indigo-950/80">
          <div className="bg-indigo-50 dark:bg-indigo-950 rounded-xl shadow-xl p-6 w-full max-w-xs mx-2">
            <div className="flex flex-col items-center text-center">
              <AlertCircle size={32} className="mb-2 text-red-600" />
              <p className="text-base font-semibold text-indigo-900 dark:text-indigo-50 mb-2">
                Delete document?
              </p>
              <p className="text-xs text-indigo-700 dark:text-indigo-200 mb-4 break-all">
                {pendingDelete.filename}
              </p>
              <div className="flex gap-2 w-full justify-center">
                <button
                  onClick={() => handleDelete(pendingDelete.filename)}
                  disabled={deletingDoc === pendingDelete.filename}
                  className="min-h-[44px] flex-1 px-3 py-2 bg-red-600 hover:bg-red-700 text-white text-xs font-medium rounded transition disabled:opacity-50 focus:outline-none focus:ring-3 focus:ring-focus"
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
                  className="min-h-[44px] flex-1 px-3 py-2 bg-indigo-300 hover:bg-indigo-500 dark:bg-indigo-700 dark:hover:bg-indigo-800 text-indigo-900 dark:text-indigo-50 text-xs font-medium rounded transition focus:outline-none focus:ring-3 focus:ring-focus"
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
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 dark:bg-indigo-950/80">
          <div className="bg-indigo-50 dark:bg-indigo-950 rounded-xl shadow-xl p-6 w-full max-w-md mx-2">
            <div className="flex flex-col items-center text-center">
              <AlertCircle size={32} className="mb-3 text-red-600" />
              <p className="text-base font-semibold text-indigo-900 dark:text-indigo-50 mb-2">
                Delete {selectedDocs.length} document
                {selectedDocs.length > 1 ? "s" : ""}?
              </p>
              <div className="w-full max-h-48 overflow-y-auto mb-4 bg-indigo-100 dark:bg-indigo-900 rounded-lg p-3">
                <ul className="text-left">
                  {selectedDocs.map(filename => (
                    <li
                      key={filename}
                      className="text-xs text-indigo-900 dark:text-indigo-50 break-all py-1.5 border-b border-indigo-300 dark:border-indigo-700 last:border-0"
                    >
                      • {filename}
                    </li>
                  ))}
                </ul>
              </div>
              <p className="text-xs text-indigo-700 dark:text-indigo-200 mb-4">
                This action cannot be undone.
              </p>
              <div className="flex gap-2 w-full justify-center">
                <button
                  onClick={() => confirmDeleteSelected(onDelete)}
                  className="min-h-[44px] flex-1 px-3 py-2 bg-red-600 hover:bg-red-700 text-white text-xs font-medium rounded transition focus:outline-none focus:ring-3 focus:ring-focus"
                >
                  Delete
                </button>
                <button
                  onClick={closeDeleteMultipleModal}
                  className="min-h-[44px] flex-1 px-3 py-2 bg-indigo-300 hover:bg-indigo-500 dark:bg-indigo-700 dark:hover:bg-indigo-800 text-indigo-900 dark:text-indigo-50 text-xs font-medium rounded transition focus:outline-none focus:ring-3 focus:ring-focus"
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
