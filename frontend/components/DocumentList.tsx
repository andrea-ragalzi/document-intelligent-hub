"use client";

import {
  FileText,
  Trash2,
  Loader,
  AlertCircle,
  MoreVertical,
  Pin,
  CheckCircle,
} from "lucide-react";
import React, { useState, useRef, useEffect } from "react";

export interface Document {
  filename: string;
  chunks_count: number;
  language?: string;
  isPinned?: boolean;
}

interface DocumentListProps {
  documents: Document[];
  deletingDoc: string | null;
  onDelete: (filename: string) => void;
  onRename?: (filename: string, currentName: string) => void;
  onPin?: (filename: string, isPinned: boolean) => void;
}

const DocumentList: React.FC<DocumentListProps> = ({
  documents,
  deletingDoc,
  onDelete,
}) => {
  const [selectedDocs, setSelectedDocs] = useState<string[]>([]);
  
  // Modalità selezione automatica quando ci sono elementi selezionati
  const isSelectionMode = selectedDocs.length > 0;
  
  // Stato per gestire il menu kebab aperto
  const [openKebabId, setOpenKebabId] = useState<string | null>(null);
  const kebabRef = useRef<{ [key: string]: HTMLDivElement | null }>({});

  // State per long-press su mobile
  const [longPressTimer, setLongPressTimer] = useState<NodeJS.Timeout | null>(
    null
  );

  // Chiudi menu kebab quando si clicca fuori
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (openKebabId && kebabRef.current[openKebabId]) {
        const kebabElement = kebabRef.current[openKebabId];
        if (kebabElement && !kebabElement.contains(event.target as Node)) {
          setOpenKebabId(null);
        }
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [openKebabId]);

  // Long press handlers per mobile
  const handleTouchStart = (filename: string) => {
    const timer = setTimeout(() => {
      setOpenKebabId(filename);
    }, 500); // 500ms per attivare long press
    setLongPressTimer(timer);
  };

  const handleTouchEnd = () => {
    if (longPressTimer) {
      clearTimeout(longPressTimer);
      setLongPressTimer(null);
    }
  };

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

  // Sort documents: pinned first, then by name
  const sortedDocuments = [...documents].sort((a, b) => {
    if (a.isPinned && !b.isPinned) return -1;
    if (!a.isPinned && b.isPinned) return 1;
    return a.filename.localeCompare(b.filename);
  });

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
      {/* Bulk Action Bar - Appare automaticamente quando ci sono selezioni */}
      {isSelectionMode && (
        <div className="sticky top-0 z-10 bg-indigo-100 dark:bg-indigo-900/50 border-2 border-indigo-300 dark:border-indigo-600 rounded-lg mb-3 p-3 shadow-md">
          <div className="flex items-center justify-between gap-2">
            <button
              onClick={handleSelectAll}
              className="text-sm text-indigo-700 dark:text-indigo-300 hover:text-indigo-900 dark:hover:text-indigo-100 transition font-semibold"
            >
              {selectedDocs.length === documents.length && documents.length > 0
                ? "Deseleziona tutto"
                : "Seleziona tutto"}
            </button>
            <button
              onClick={handleDeleteSelected}
              className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-sm font-semibold rounded-lg transition-all duration-200 shadow-sm hover:shadow-md flex items-center gap-2"
            >
              <Trash2 size={16} />
              <span>Elimina ({selectedDocs.length})</span>
            </button>
          </div>
        </div>
      )}
      
      <div className="space-y-2">
        <div className="space-y-2 max-h-64 overflow-y-auto">
          {sortedDocuments.length === 0 ? (
            <div className="text-center py-8 text-gray-500 dark:text-gray-400 text-sm">
              No documents uploaded yet
            </div>
          ) : (
            sortedDocuments.map((doc) => {
              const isSelected = selectedDocs.includes(doc.filename);
              const isKebabOpen = openKebabId === doc.filename;

              return (
                <div
                  key={doc.filename}
                  className={`group relative rounded-lg p-3 transform hover:scale-[1.01] transition-all duration-200 ease-in-out hover:shadow-sm ${
                    isSelected
                      ? "bg-indigo-100 dark:bg-indigo-900/50 border-2 border-indigo-500 dark:border-indigo-400"
                      : "bg-white dark:bg-gray-700 border-2 border-gray-200 dark:border-gray-600 hover:bg-indigo-50 dark:hover:bg-gray-600 hover:border-indigo-200 dark:hover:border-indigo-800"
                  } cursor-pointer`}
                  onClick={() => {
                    if (isSelectionMode) {
                      handleSelect(doc.filename);
                    }
                  }}
                  onTouchStart={() =>
                    !isSelectionMode && handleTouchStart(doc.filename)
                  }
                  onTouchEnd={handleTouchEnd}
                  onContextMenu={(e) => {
                    if (!isSelectionMode) {
                      e.preventDefault();
                      setOpenKebabId(doc.filename);
                    }
                  }}
                >
                  <div className="flex items-center gap-3">
                    {/* Indicatore visivo di selezione - Solo elementi selezionati */}
                    {isSelected && (
                      <div className="flex-shrink-0 h-6 w-6 flex items-center justify-center rounded-full bg-indigo-600 dark:bg-indigo-500">
                        <CheckCircle size={16} className="text-white" />
                      </div>
                    )}

                    {/* Indicatore Pin - Solo documenti fissati */}
                    {!isSelected && doc.isPinned && (
                      <div className="flex-shrink-0 h-6 w-6 flex items-center justify-center">
                        <Pin
                          size={14}
                          className="text-indigo-600 dark:text-indigo-400"
                          fill="currentColor"
                        />
                      </div>
                    )}

                    {/* Icona documento */}
                    {!isSelected && !doc.isPinned && (
                      <div className="flex-shrink-0 w-6 h-6 bg-indigo-100 dark:bg-indigo-900/30 rounded flex items-center justify-center">
                        <FileText size={14} className="text-indigo-600" />
                      </div>
                    )}

                    {/* Contenuto documento */}
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-semibold text-gray-900 dark:text-gray-100 truncate">
                        {doc.filename}
                      </p>
                      <div className="flex items-center gap-2 mt-0.5">
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

                    {/* Menu Kebab - Solo desktop, nascosto su mobile */}
                    {!isSelectionMode && (
                      <div
                        className="relative flex-shrink-0"
                        ref={(el) => {
                          kebabRef.current[doc.filename] = el;
                        }}
                      >
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setOpenKebabId(
                              isKebabOpen ? null : doc.filename
                            );
                          }}
                          className="h-7 w-7 flex items-center justify-center text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-600 rounded transition-all duration-200 ease-in-out opacity-0 group-hover:opacity-100 hidden md:flex"
                          title="Opzioni"
                        >
                          <MoreVertical size={16} />
                        </button>

                        {/* Dropdown Menu - Solo Elimina per documenti */}
                        {isKebabOpen && (
                          <div
                            className="absolute right-0 top-8 z-50 w-48 bg-white dark:bg-gray-800 rounded-lg shadow-xl border-2 border-gray-200 dark:border-gray-600 py-1"
                            onClick={(e) => e.stopPropagation()}
                          >
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                setOpenKebabId(null);
                                openDeleteModal(doc);
                              }}
                              className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-gray-700 dark:text-gray-200 hover:bg-red-50 dark:hover:bg-red-900/30 transition-colors duration-200"
                            >
                              <Trash2 size={16} className="text-red-600" />
                              <span className="font-medium">Elimina</span>
                            </button>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              );
            })
          )}
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
