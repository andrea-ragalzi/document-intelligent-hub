import type { SavedConversation } from "@/lib/types";
import {
  Trash2,
  Edit,
  AlertCircle,
  MoreVertical,
  Pin,
  CheckCircle,
} from "lucide-react";
import { useState, useRef, useEffect } from "react";
import { createPortal } from "react-dom";

interface ConversationListProps {
  conversations: SavedConversation[];
  currentConversationId?: string | null;
  onLoad: (conv: SavedConversation) => void;
  onDelete: (id: string, name: string) => void;
  onRename: (id: string, currentName: string) => void;
  onPin: (id: string, isPinned: boolean) => void;
}

// Function to generate conversation preview
const _getConversationPreview = (conv: SavedConversation): string => {
  if (conv.history.length > 0) {
    const firstUserMessage = conv.history.find((msg) => msg.type === "user");
    if (firstUserMessage) {
      const preview = firstUserMessage.text.substring(0, 60);
      return preview.length < firstUserMessage.text.length
        ? `${preview}...`
        : preview;
    }
  }
  return "No messages yet";
};

export const ConversationList: React.FC<ConversationListProps> = ({
  conversations,
  currentConversationId,
  onLoad,
  onDelete,
  onRename,
  onPin,
}) => {
  const [selectedConvs, setSelectedConvs] = useState<string[]>([]);
  const [deleteMultipleModalOpen, setDeleteMultipleModalOpen] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [pendingDelete, setPendingDelete] = useState<SavedConversation | null>(
    null
  );

  // Desktop kebab menu state
  const [openKebabId, setOpenKebabId] = useState<string | null>(null);
  const [menuPosition, setMenuPosition] = useState<{
    top: number;
    right: number;
  } | null>(null);
  const kebabRef = useRef<{ [key: string]: HTMLDivElement | null }>({});
  const menuRef = useRef<HTMLDivElement | null>(null);

  // Long press tracking for mobile
  const [longPressTimer, setLongPressTimer] = useState<NodeJS.Timeout | null>(
    null
  );

  // Drag state for mobile menu
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
          console.error("Context menu action failed:", error)
        );
      }
    } finally {
      closeContextMenu();
    }
  };

  // Auto-enable selection mode when items are selected
  const isSelectionMode = selectedConvs.length > 0;

  // Close kebab menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (!openKebabId) {
        return;
      }

      const kebabElement = kebabRef.current[openKebabId];
      const menuElement = menuRef.current;
      const targetNode = event.target as Node;

      const clickedInsideTrigger =
        kebabElement && kebabElement.contains(targetNode);
      const clickedInsideMenu = menuElement && menuElement.contains(targetNode);

      if (!clickedInsideTrigger && !clickedInsideMenu) {
        closeContextMenu();
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [openKebabId]);

  const handleSelect = (id: string) => {
    setSelectedConvs((prev) =>
      prev.includes(id) ? prev.filter((convId) => convId !== id) : [...prev, id]
    );
  };

  const handleSelectAll = () => {
    if (selectedConvs.length === conversations.length) {
      setSelectedConvs([]);
    } else {
      setSelectedConvs(conversations.map((c) => c.id));
    }
  };

  // Long press handlers for mobile
  const handleTouchStart = (e: React.TouchEvent, convId: string) => {
    if (isSelectionMode) return;

    const target = e.currentTarget;
    const timer = setTimeout(() => {
      if (!target) {
        return;
      }
      // Open menu on long press
      const rect = target.getBoundingClientRect();
      setMenuPosition({
        top: rect.bottom + window.scrollY + 4,
        right: window.innerWidth - rect.right + window.scrollX,
      });
      setOpenKebabId(convId);
    }, 500); // 500ms long press
    setLongPressTimer(timer);
  };

  const handleTouchEnd = () => {
    if (longPressTimer) {
      clearTimeout(longPressTimer);
      setLongPressTimer(null);
    }
  };

  // Drag handlers for mobile menu
  const handleDragStart = (e: React.TouchEvent) => {
    setIsDragging(true);
    dragStartY.current = e.touches[0].clientY;
  };

  const handleDragMove = (e: React.TouchEvent) => {
    if (!isDragging) return;
    const currentY = e.touches[0].clientY;
    const deltaY = currentY - dragStartY.current;
    if (deltaY > 0) {
      // Only allow dragging down
      setDragY(deltaY);
    }
  };

  const handleDragEnd = () => {
    if (dragY > 100) {
      // If dragged more than 100px, close menu
      closeContextMenu();
    } else {
      setIsDragging(false);
      setDragY(0);
    }
  };

  const openDeleteModal = (conv: SavedConversation) => {
    setPendingDelete(conv);
    setModalOpen(true);
  };

  const closeDeleteModal = () => {
    setModalOpen(false);
    setPendingDelete(null);
  };

  const handleDelete = () => {
    if (pendingDelete) {
      onDelete(pendingDelete.id, pendingDelete.name);
      closeDeleteModal();
    }
  };

  const handleDeleteSelected = () => {
    if (selectedConvs.length === 0) return;
    setDeleteMultipleModalOpen(true);
  };

  const confirmDeleteSelected = () => {
    // Delete all selected conversations
    selectedConvs.forEach((id) => {
      const conv = conversations.find((c) => c.id === id);
      if (conv) {
        onDelete(conv.id, conv.name);
      }
    });
    // Reset selection
    setSelectedConvs([]);
    setDeleteMultipleModalOpen(false);
  };

  // Ordina conversazioni: prima le fissate, poi per data decrescente - LISTA PIATTA
  const sortedConversations = [...conversations].sort((a, b) => {
    // Prima ordina per isPinned
    if (a.isPinned && !b.isPinned) return -1;
    if (!a.isPinned && b.isPinned) return 1;
    // Poi ordina per data (più recenti in alto)
    return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime();
  });

  return (
    <section className="font-[Inter]">
      <h2 className="text-base font-bold text-gray-800 dark:text-gray-100 mb-4 px-2">
        Conversations
      </h2>

      {/* Bulk Action Bar - Automatically appears when there are selections */}
      {isSelectionMode && (
        <div className="sticky top-0 z-10 bg-indigo-100 dark:bg-indigo-900/50 border-2 border-indigo-300 dark:border-indigo-600 rounded-lg mb-3 p-3 shadow-md">
          <div className="flex items-center justify-between gap-2">
            <button
              onClick={handleSelectAll}
              className="text-sm text-indigo-700 dark:text-indigo-300 hover:text-indigo-900 dark:hover:text-indigo-100 transition font-semibold"
            >
              {selectedConvs.length === conversations.length
                ? "Deselect All"
                : "Select All"}
            </button>
            <button
              onClick={handleDeleteSelected}
              className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-sm font-semibold rounded-lg transition-all duration-200 shadow-sm hover:shadow-md flex items-center gap-2"
            >
              <Trash2 size={16} />
              <span>Delete ({selectedConvs.length})</span>
            </button>
          </div>
        </div>
      )}

      {/* Flat sorted list (pinned first, then by date) */}
      <div className="space-y-1">
        {conversations.length === 0 ? (
          <p className="text-sm text-gray-500 dark:text-gray-400 italic px-2 py-8 text-center">
            No saved conversations
          </p>
        ) : (
          sortedConversations.map((conv) => {
            const isActive = currentConversationId === conv.id;
            const isSelected = selectedConvs.includes(conv.id);
            const isKebabOpen = openKebabId === conv.id;

            return (
              <div
                key={conv.id}
                className={`group relative rounded-lg p-3 transform hover:scale-[1.01] transition-all duration-200 ease-in-out hover:shadow-sm ${
                  isSelected
                    ? "bg-indigo-100 dark:bg-indigo-900/50 border-2 border-indigo-500 dark:border-indigo-400"
                    : isActive
                    ? "bg-indigo-50 dark:bg-indigo-900/30 border-2 border-indigo-300 dark:border-indigo-700"
                    : "bg-white dark:bg-gray-700 border-2 border-gray-200 dark:border-gray-600 hover:bg-indigo-50 dark:hover:bg-gray-600 hover:border-indigo-200 dark:hover:border-indigo-800"
                } cursor-pointer`}
                onClick={() => {
                  if (isSelectionMode) {
                    handleSelect(conv.id);
                  } else {
                    onLoad(conv);
                  }
                }}
                onTouchStart={(e) => handleTouchStart(e, conv.id)}
                onTouchEnd={handleTouchEnd}
                onContextMenu={(e) => {
                  if (!isSelectionMode) {
                    e.preventDefault();
                    const rect = e.currentTarget.getBoundingClientRect();
                    setMenuPosition({
                      top: rect.bottom + window.scrollY + 4,
                      right: window.innerWidth - rect.right + window.scrollX,
                    });
                    setOpenKebabId(conv.id);
                  }
                }}
              >
                <div className="flex items-start gap-2">
                  {/* Indicatore visivo di selezione - Solo elementi selezionati */}
                  {isSelected && (
                    <div className="flex-shrink-0 h-6 w-6 flex items-center justify-center rounded-full bg-indigo-600 dark:bg-indigo-500 mt-1">
                      <CheckCircle size={16} className="text-white" />
                    </div>
                  )}

                  {/* Contenuto conversazione */}
                  <div className="flex-1 min-w-0">
                    <p
                      className={`font-semibold text-sm truncate transition-colors duration-200 ${
                        isActive
                          ? "text-indigo-700 dark:text-indigo-200"
                          : "text-gray-900 dark:text-gray-100 group-hover:text-indigo-700 dark:group-hover:text-indigo-300"
                      }`}
                    >
                      {conv.name}
                    </p>
                    {/* Timestamp */}
                    <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                      {conv.timestamp}
                    </p>
                  </div>

                  {/* Contenitore unificato: Pin (default) o Menu Kebab (hover) - Solo desktop */}
                  {!isSelectionMode && (
                    <div
                      className="relative flex-shrink-0 h-7 w-7"
                      ref={(el) => {
                        kebabRef.current[conv.id] = el;
                      }}
                    >
                      {/* Indicatore Pin - Visibile di default, nascosto all'hover */}
                      {!isSelected && conv.isPinned && (
                        <div className="absolute inset-0 flex items-center justify-center md:group-hover:hidden">
                          <Pin
                            size={14}
                            className="text-indigo-600 dark:text-indigo-400"
                            fill="currentColor"
                          />
                        </div>
                      )}

                      {/* Menu Kebab - Desktop only: visible on hover */}
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
                                window.innerWidth - rect.right + window.scrollX,
                            });
                            setOpenKebabId(conv.id);
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

      {/* Dropdown Menu - Rendered at root level to avoid z-index issues */}
      {openKebabId &&
        menuPosition &&
        createPortal(
          <>
            {/* Backdrop for mobile */}
            <div
              className="fixed inset-0 bg-black/90 z-[100] md:hidden"
              onClick={(e) => {
                e.stopPropagation();
                closeContextMenu();
              }}
            />
            {/* Menu - Mobile: draggable bottom sheet, Desktop: positioned dropdown */}
            <div
              className="fixed inset-x-0 md:inset-x-auto md:bottom-auto bg-gradient-to-b from-slate-900 to-black rounded-t-3xl md:rounded-lg shadow-2xl border-0 z-[110] transition-transform overflow-hidden"
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
                const conv = conversations.find((c) => c.id === openKebabId);
                if (!conv) return null;

                return (
                  <div className="flex flex-col gap-1 pt-3 pb-4">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        runActionAndCloseMenu(() =>
                          onPin(conv.id, !conv.isPinned)
                        );
                      }}
                      className="w-full flex items-center gap-3 px-5 py-4 text-lg text-white hover:bg-white/10 transition-colors duration-200"
                    >
                      <Pin
                        size={18}
                        className={
                          conv.isPinned ? "text-indigo-300" : "text-white/80"
                        }
                        fill={conv.isPinned ? "currentColor" : "none"}
                      />
                      <span className="font-semibold tracking-wide">
                        {conv.isPinned ? "Unpin" : "Pin"}
                      </span>
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        runActionAndCloseMenu(() =>
                          onRename(conv.id, conv.name)
                        );
                      }}
                      className="w-full flex items-center gap-3 px-5 py-4 text-lg text-white hover:bg-white/10 transition-colors duration-200"
                    >
                      <Edit size={18} className="text-white/80" />
                      <span className="font-semibold tracking-wide">
                        Rename
                      </span>
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        runActionAndCloseMenu(() => openDeleteModal(conv));
                      }}
                      className="w-full flex items-center gap-3 px-5 py-4 text-lg text-white hover:bg-white/10 transition-colors duration-200"
                    >
                      <Trash2 size={18} className="text-white/80" />
                      <span className="font-semibold tracking-wide">
                        Delete
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

      {/* Delete Single Conversation Modal */}
      {modalOpen && pendingDelete && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl p-6 w-full max-w-xs mx-2">
            <div className="flex flex-col items-center text-center">
              <AlertCircle size={32} className="mb-2 text-red-600" />
              <p className="text-base font-semibold text-gray-800 dark:text-white mb-2">
                Delete conversation?
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400 mb-4 break-all">
                {pendingDelete.name}
              </p>
              <div className="flex gap-2 w-full justify-center">
                <button
                  onClick={handleDelete}
                  className="flex-1 px-3 py-2 bg-red-600 hover:bg-red-700 text-white text-xs font-medium rounded transition"
                >
                  Delete
                </button>
                <button
                  onClick={closeDeleteModal}
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
                Delete {selectedConvs.length} conversation
                {selectedConvs.length > 1 ? "s" : ""}?
              </p>
              <div className="w-full max-h-48 overflow-y-auto mb-4 bg-gray-50 dark:bg-gray-900/50 rounded-lg p-3">
                <ul className="text-left">
                  {selectedConvs.map((id) => {
                    const conv = conversations.find((c) => c.id === id);
                    return conv ? (
                      <li
                        key={id}
                        className="text-xs text-gray-700 dark:text-gray-300 break-all py-1.5 border-b border-gray-200 dark:border-gray-700 last:border-0"
                      >
                        • {conv.name}
                      </li>
                    ) : null;
                  })}
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
    </section>
  );
};
