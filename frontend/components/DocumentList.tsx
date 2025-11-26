"use client";

import {
  FileText,
  Trash2,
  Loader,
  AlertCircle,
  MoreVertical,
  CheckCircle,
} from "lucide-react";
import React, { useState, useRef, useEffect } from "react";
import { createPortal } from "react-dom";

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
  const [selectedDocs, setSelectedDocs] = useState<string[]>([]);

  // Safety check: ensure documents is always an array
  const safeDocuments = documents || [];

  // Automatic selection mode when items are selected
  const isSelectionMode = selectedDocs.length > 0;

  // Desktop kebab menu state
  const [openKebabId, setOpenKebabId] = useState<string | null>(null);
  const [menuPosition, setMenuPosition] = useState<{
    top: number;
    right: number;
  } | null>(null);
  const kebabRef = useRef<{ [key: string]: HTMLDivElement | null }>({});
  const menuRef = useRef<HTMLDivElement | null>(null);

  // Mobile gestures: long-press and drag
  const [longPressTimer, setLongPressTimer] = useState<NodeJS.Timeout | null>(
    null
  );
  const [dragY, setDragY] = useState(0);
  const [isDragging, setIsDragging] = useState(false);
  const dragStartY = useRef(0);

  const closeContextMenu = () => {
    setOpenKebabId(null);
    setMenuPosition(null);
    setDragY(0);
    setIsDragging(false);
    menuRef.current = null;
  };

  const runActionAndCloseMenu = (action: () => void | Promise<void>) => {
    try {
      const result = action();
      if (result instanceof Promise) {
        result.catch((error) =>
          console.error("Document menu action failed:", error)
        );
      }
    } finally {
      closeContextMenu();
    }
  };

  // Touch handlers for mobile gestures
  const handleTouchStart = (e: React.TouchEvent, filename: string) => {
    if (isSelectionMode) return;

    const target = e.currentTarget;
    const timer = setTimeout(() => {
      if (!target) {
        return;
      }
      const rect = target.getBoundingClientRect();
      setMenuPosition({
        top: rect.bottom + window.scrollY + 8,
        right: window.innerWidth - rect.right + window.scrollX,
      });
      setOpenKebabId(filename);
    }, 200);

    setLongPressTimer(timer);
  };

  const handleTouchEnd = () => {
    if (longPressTimer) {
      clearTimeout(longPressTimer);
      setLongPressTimer(null);
    }
  };

  const handleDragStart = (e: React.TouchEvent) => {
    setIsDragging(true);
    dragStartY.current = e.touches[0].clientY;
  };

  const handleDragMove = (e: React.TouchEvent) => {
    if (!isDragging) return;

    const deltaY = e.touches[0].clientY - dragStartY.current;
    if (deltaY > 0) {
      setDragY(deltaY);
    }
  };

  const handleDragEnd = () => {
    if (dragY > 100) {
      closeContextMenu();
    } else {
      setIsDragging(false);
      setDragY(0);
    }
  };

  // Close kebab menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (!openKebabId) {
        return;
      }

      const kebabElement = kebabRef.current[openKebabId];
      const menuElement = menuRef.current;
      const targetNode = event.target as Node;

      const clickedInsideTrigger = kebabElement?.contains(targetNode);
      const clickedInsideMenu = menuElement?.contains(targetNode);

      if (!clickedInsideTrigger && !clickedInsideMenu) {
        closeContextMenu();
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [openKebabId]);

  const handleSelect = (filename: string) => {
    setSelectedDocs((prev) =>
      prev.includes(filename)
        ? prev.filter((f) => f !== filename)
        : [...prev, filename]
    );
  };

  const handleSelectAll = () => {
    if (selectedDocs.length === safeDocuments.length) {
      setSelectedDocs([]);
    } else {
      setSelectedDocs(safeDocuments.map((d) => d.filename));
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

  // Sort documents by name (alphabetically)
  const sortedDocuments = [...safeDocuments].sort((a, b) =>
    a.filename.localeCompare(b.filename)
  );

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
      {/* Bulk Action Bar - Automatically appears when there are selections */}
      {isSelectionMode && (
        <div className="sticky top-0 z-10 bg-indigo-100 dark:bg-indigo-900/50 border-2 border-indigo-300 dark:border-indigo-600 rounded-lg mb-3 p-3 shadow-md">
          <div className="flex items-center justify-between gap-2">
            <button
              onClick={handleSelectAll}
              className="text-sm text-indigo-700 dark:text-indigo-300 hover:text-indigo-900 dark:hover:text-indigo-100 transition font-semibold"
            >
              {selectedDocs.length === safeDocuments.length &&
              safeDocuments.length > 0
                ? "Deselect All"
                : "Select All"}
            </button>
            <button
              onClick={handleDeleteSelected}
              disabled={!isServerOnline}
              className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-sm font-semibold rounded-lg transition-all duration-200 shadow-sm hover:shadow-md flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
              title={
                !isServerOnline
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
                  onTouchStart={(e) => handleTouchStart(e, doc.filename)}
                  onTouchEnd={handleTouchEnd}
                  onContextMenu={(e) => {
                    if (!isSelectionMode) {
                      e.preventDefault();
                      const rect = e.currentTarget.getBoundingClientRect();
                      setMenuPosition({
                        top: rect.bottom + window.scrollY + 8,
                        right: window.innerWidth - rect.right + window.scrollX,
                      });
                      setOpenKebabId(doc.filename);
                    }
                  }}
                >
                  <div className="flex items-center gap-3">
                    {/* Selection indicator - Only for selected items */}
                    {isSelected && (
                      <div className="flex-shrink-0 h-6 w-6 flex items-center justify-center rounded-full bg-indigo-600 dark:bg-indigo-500">
                        <CheckCircle size={16} className="text-white" />
                      </div>
                    )}

                    {/* Document icon - Always visible when not selected */}
                    {!isSelected && (
                      <div className="flex-shrink-0 w-6 h-6 bg-indigo-100 dark:bg-indigo-900/30 rounded flex items-center justify-center">
                        <FileText size={14} className="text-indigo-600" />
                      </div>
                    )}

                    {/* Document content */}
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

                    {/* Unified container: Kebab menu (hover on desktop) */}
                    {!isSelectionMode && (
                      <div
                        className="relative flex-shrink-0 h-7 w-7"
                        ref={(el) => {
                          kebabRef.current[doc.filename] = el;
                        }}
                      >
                        {/* Kebab menu - Visible on mobile tap, visible on hover on desktop */}
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            if (isKebabOpen) {
                              closeContextMenu();
                            } else {
                              const rect =
                                e.currentTarget.getBoundingClientRect();
                              setMenuPosition({
                                top: rect.bottom + window.scrollY + 4,
                                right:
                                  window.innerWidth -
                                  rect.right +
                                  window.scrollX,
                              });
                              setOpenKebabId(doc.filename);
                            }
                          }}
                          className="absolute inset-0 items-center justify-center text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-600 rounded transition-all duration-200 ease-in-out opacity-0 group-hover:opacity-100 hidden md:flex"
                          title="Options"
                        >
                          <MoreVertical size={16} />
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* Dropdown Menu - Rendered at root level to avoid z-index issues */}
      {openKebabId &&
        menuPosition &&
        createPortal(
          <>
            {/* Backdrop for mobile */}
            <div
              className="fixed inset-0 bg-black/70 dark:bg-indigo-950/90 z-[100] md:hidden"
              onClick={(e) => {
                e.stopPropagation();
                closeContextMenu();
              }}
            />
            {/* Menu - Mobile: draggable bottom sheet, Desktop: positioned dropdown */}
            <div
              className="fixed inset-x-0 md:inset-x-auto md:bottom-auto bg-gradient-to-b from-indigo-900 to-indigo-950 dark:from-slate-900 dark:to-black rounded-t-3xl md:rounded-lg shadow-2xl border-0 z-[110] transition-transform overflow-hidden"
              ref={(node) => {
                menuRef.current = node;
              }}
              style={{
                bottom: window.innerWidth < 768 ? `${-dragY}px` : undefined,
                height: window.innerWidth < 768 ? "35vh" : undefined,
                top:
                  window.innerWidth >= 768
                    ? `${menuPosition.top}px`
                    : undefined,
                right:
                  window.innerWidth >= 768
                    ? `${menuPosition.right}px`
                    : undefined,
                width: window.innerWidth >= 768 ? "12rem" : undefined,
              }}
            >
              {/* Drag handle for mobile */}
              <div
                className="md:hidden flex justify-center pt-4 pb-2 cursor-grab active:cursor-grabbing"
                onTouchStart={handleDragStart}
                onTouchMove={handleDragMove}
                onTouchEnd={handleDragEnd}
              >
                <div className="w-10 h-1 bg-white/60 rounded-full" />
              </div>

              {(() => {
                const doc = safeDocuments.find(
                  (d) => d.filename === openKebabId
                );
                if (!doc) return null;

                return (
                  <div className="flex flex-col gap-1 pt-3 pb-4">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        if (isServerOnline) {
                          runActionAndCloseMenu(() => openDeleteModal(doc));
                        }
                      }}
                      disabled={!isServerOnline}
                      className="w-full flex items-center gap-3 px-5 py-4 text-lg text-white hover:bg-white/10 transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                      title={
                        !isServerOnline
                          ? "Server offline - delete unavailable"
                          : "Delete document"
                      }
                    >
                      <Trash2 size={18} className="text-white/80" />
                      <span className="font-semibold tracking-wide">
                        {!isServerOnline ? "Delete (Offline)" : "Delete"}
                      </span>
                    </button>

                    {/* Safe area padding for iOS */}
                    <div className="md:hidden h-4" />
                  </div>
                );
              })()}
            </div>
          </>,
          document.body
        )}

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
                  {selectedDocs.map((filename) => (
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
                  onClick={confirmDeleteSelected}
                  className="min-h-[44px] flex-1 px-3 py-2 bg-red-600 hover:bg-red-700 text-white text-xs font-medium rounded transition focus:outline-none focus:ring-3 focus:ring-focus"
                >
                  Delete
                </button>
                <button
                  onClick={() => setDeleteMultipleModalOpen(false)}
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
