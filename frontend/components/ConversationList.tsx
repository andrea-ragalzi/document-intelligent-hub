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
import { MobileActionSheet } from "./MobileActionSheet";

interface ConversationListProps {
  conversations: SavedConversation[];
  currentConversationId?: string | null;
  onLoad: (conv: SavedConversation) => void;
  onDelete: (id: string, name: string) => void;
  onRename: (id: string, currentName: string) => void;
  onPin: (id: string, isPinned: boolean) => void;
}

// Funzione per raggruppare le conversazioni per data
const _groupConversationsByDate = (conversations: SavedConversation[]) => {
  const today = new Date();
  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);

  const groups: { [key: string]: SavedConversation[] } = {
    Oggi: [],
    Ieri: [],
    "Ultimi 7 giorni": [],
    "Ultimi 30 giorni": [],
    "Più vecchi": [],
  };

  conversations.forEach((conv) => {
    const convDate = new Date(conv.timestamp);
    const diffTime = today.getTime() - convDate.getTime();
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays === 0) {
      groups["Oggi"].push(conv);
    } else if (diffDays === 1) {
      groups["Ieri"].push(conv);
    } else if (diffDays <= 7) {
      groups["Ultimi 7 giorni"].push(conv);
    } else if (diffDays <= 30) {
      groups["Ultimi 30 giorni"].push(conv);
    } else {
      groups["Più vecchi"].push(conv);
    }
  });

  // Rimuovi gruppi vuoti
  return Object.entries(groups).filter(([_, convs]) => convs.length > 0);
};

// Funzione per generare anteprima del contenuto
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

interface ConversationListProps {
  conversations: SavedConversation[];
  onLoad: (conv: SavedConversation) => void;
  onDelete: (id: string, name: string) => void;
  onRename: (id: string, currentName: string) => void;
}

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
  
  // Mobile Action Sheet state
  const [actionSheetOpen, setActionSheetOpen] = useState(false);
  const [actionSheetTarget, setActionSheetTarget] = useState<string | null>(null);
  
  // Desktop kebab menu state
  const [openKebabId, setOpenKebabId] = useState<string | null>(null);
  const kebabRef = useRef<{ [key: string]: HTMLDivElement | null }>({});

  // Long press tracking for mobile
  const [longPressTimer, setLongPressTimer] = useState<NodeJS.Timeout | null>(
    null
  );
  
  // Auto-enable selection mode when items are selected
  const isSelectionMode = selectedConvs.length > 0;
  const _longPressTarget = useState<string | null>(null)[0]; // Prefix unused var

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

  // Long press handlers per mobile - apre Action Sheet
  const handleTouchStart = (conv: SavedConversation) => {
    const timer = setTimeout(() => {
      // Apri Action Sheet su mobile
      setActionSheetTarget(conv.id);
      setActionSheetOpen(true);
    }, 500); // 500ms per attivare long press
    setLongPressTimer(timer);
  };

  const handleTouchEnd = () => {
    if (longPressTimer) {
      clearTimeout(longPressTimer);
      setLongPressTimer(null);
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
        Conversazioni
      </h2>

      {/* Bulk Action Bar - Appare automaticamente quando ci sono selezioni */}
      {isSelectionMode && (
        <div className="sticky top-0 z-10 bg-indigo-100 dark:bg-indigo-900/50 border-2 border-indigo-300 dark:border-indigo-600 rounded-lg mb-3 p-3 shadow-md">
          <div className="flex items-center justify-between gap-2">
            <button
              onClick={handleSelectAll}
              className="text-sm text-indigo-700 dark:text-indigo-300 hover:text-indigo-900 dark:hover:text-indigo-100 transition font-semibold"
            >
              {selectedConvs.length === conversations.length
                ? "Deseleziona tutto"
                : "Seleziona tutto"}
            </button>
            <button
              onClick={handleDeleteSelected}
              className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-sm font-semibold rounded-lg transition-all duration-200 shadow-sm hover:shadow-md flex items-center gap-2"
            >
              <Trash2 size={16} />
              <span>Elimina ({selectedConvs.length})</span>
            </button>
          </div>
        </div>
      )}

      {/* Lista piatta ordinata (pinned first, poi per data) */}
      <div className="space-y-1">
        {conversations.length === 0 ? (
          <p className="text-sm text-gray-500 dark:text-gray-400 italic px-2 py-8 text-center">
            Nessuna conversazione salvata
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
                onTouchStart={() => !isSelectionMode && handleTouchStart(conv)}
                onTouchEnd={handleTouchEnd}
                onContextMenu={(e) => {
                  if (!isSelectionMode) {
                    e.preventDefault();
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

                  {/* Indicatore Pin - Solo conversazioni fissate */}
                  {!isSelected && conv.isPinned && (
                    <div className="flex-shrink-0 h-6 w-6 flex items-center justify-center mt-1">
                      <Pin
                        size={14}
                        className="text-indigo-600 dark:text-indigo-400"
                        fill="currentColor"
                      />
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

                  {/* Menu Kebab - Solo desktop, nascosto su mobile */}
                  {!isSelectionMode && (
                    <div
                      className="relative flex-shrink-0"
                      ref={(el) => {
                        kebabRef.current[conv.id] = el;
                      }}
                    >
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setOpenKebabId(isKebabOpen ? null : conv.id);
                        }}
                        className="h-7 w-7 flex items-center justify-center text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-600 rounded transition-all duration-200 ease-in-out opacity-0 group-hover:opacity-100 hidden md:flex"
                        title="Opzioni"
                      >
                        <MoreVertical size={16} />
                      </button>

                      {/* Dropdown Menu */}
                      {isKebabOpen && (
                        <div className="absolute right-0 top-8 z-50 w-48 bg-white dark:bg-gray-800 rounded-lg shadow-xl border-2 border-gray-200 dark:border-gray-600 py-1">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setOpenKebabId(null);
                              onPin(conv.id, !conv.isPinned);
                            }}
                            className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors duration-200"
                          >
                            <Pin
                              size={16}
                              className={
                                conv.isPinned
                                  ? "text-indigo-600"
                                  : "text-gray-600"
                              }
                              fill={conv.isPinned ? "currentColor" : "none"}
                            />
                            <span className="font-medium">
                              {conv.isPinned ? "Sgancia" : "Fissa"}
                            </span>
                          </button>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setOpenKebabId(null);
                              onRename(conv.id, conv.name);
                            }}
                            className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors duration-200"
                          >
                            <Edit size={16} className="text-green-600" />
                            <span className="font-medium">Rinomina</span>
                          </button>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setOpenKebabId(null);
                              openDeleteModal(conv);
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
      
      {/* Mobile Action Sheet */}
      <MobileActionSheet
        isOpen={actionSheetOpen}
        onClose={() => setActionSheetOpen(false)}
        title={
          actionSheetTarget
            ? conversations.find((c) => c.id === actionSheetTarget)?.name || "Conversazione"
            : "Conversazione"
        }
        options={[
          {
            icon: <Pin size={20} />,
            label: actionSheetTarget && conversations.find((c) => c.id === actionSheetTarget)?.isPinned
              ? "Sgancia"
              : "Fissa",
            onClick: () => {
              if (actionSheetTarget) {
                const conv = conversations.find((c) => c.id === actionSheetTarget);
                if (conv) {
                  onPin(conv.id, !conv.isPinned);
                }
              }
              setActionSheetOpen(false);
            },
          },
          {
            icon: <Edit size={20} />,
            label: "Rinomina",
            onClick: () => {
              if (actionSheetTarget) {
                const conv = conversations.find((c) => c.id === actionSheetTarget);
                if (conv) {
                  onRename(conv.id, conv.name);
                }
              }
              setActionSheetOpen(false);
            },
          },
          {
            icon: <Trash2 size={20} />,
            label: "Elimina",
            onClick: () => {
              if (actionSheetTarget) {
                const conv = conversations.find((c) => c.id === actionSheetTarget);
                if (conv) {
                  onDelete(conv.id, conv.name);
                }
              }
              setActionSheetOpen(false);
            },
            variant: "danger" as const,
          },
        ]}
      />

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
