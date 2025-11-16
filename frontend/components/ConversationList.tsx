import type { SavedConversation } from "@/lib/types";
import {
  Trash2,
  Archive,
  Edit,
  Square,
  CheckSquare,
  AlertCircle,
} from "lucide-react";
import { useState } from "react";

interface ConversationListProps {
  conversations: SavedConversation[];
  onLoad: (conv: SavedConversation) => void;
  onDelete: (id: string, name: string) => void;
  onRename: (id: string, currentName: string) => void;
}

export const ConversationList: React.FC<ConversationListProps> = ({
  conversations,
  onLoad,
  onDelete,
  onRename,
}) => {
  const [selectedConvs, setSelectedConvs] = useState<string[]>([]);
  const [deleteMultipleModalOpen, setDeleteMultipleModalOpen] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [pendingDelete, setPendingDelete] = useState<SavedConversation | null>(
    null
  );

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

  return (
    <section className="pt-4">
      <h2 className="text-lg font-bold text-gray-800 dark:text-white mb-3 flex items-center border-b border-gray-100 dark:border-gray-700 pb-2">
        <Archive size={16} className="mr-2 text-blue-600" /> Saved Conversations
      </h2>
      {conversations.length > 0 && (
        <div className="flex items-center justify-between gap-2 mb-3 px-1">
          <button
            onClick={handleSelectAll}
            className="flex items-center gap-2 hover:opacity-70 transition"
          >
            {selectedConvs.length === conversations.length ? (
              <CheckSquare size={16} className="text-blue-600" />
            ) : (
              <Square size={16} className="text-gray-400" />
            )}
            <span className="text-xs text-gray-700 dark:text-gray-200 select-none">
              Select all
            </span>
          </button>
          {selectedConvs.length > 0 && (
            <button
              onClick={handleDeleteSelected}
              className="px-3 py-1.5 bg-red-600 hover:bg-red-700 text-white text-xs font-medium rounded transition"
            >
              Delete selected ({selectedConvs.length})
            </button>
          )}
        </div>
      )}
      <div className="space-y-2 max-h-64 overflow-y-auto pr-2">
        {conversations.length === 0 ? (
          <p className="text-sm text-gray-500 dark:text-gray-400 italic">
            No saved conversations.
          </p>
        ) : (
          conversations.map((conv) => (
            <div
              key={conv.id}
              className="group relative bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-3 hover:shadow-md transition-all"
            >
              <div className="flex items-center gap-3">
                <div
                  onClick={() => onLoad(conv)}
                  className="flex-1 min-w-0 cursor-pointer"
                >
                  <p className="font-semibold text-sm text-gray-800 dark:text-white truncate group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                    {conv.name}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                    {conv.timestamp}
                  </p>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleSelect(conv.id);
                  }}
                  className="flex-shrink-0 p-1 hover:opacity-70 transition"
                  title="Select conversation"
                >
                  {selectedConvs.includes(conv.id) ? (
                    <CheckSquare size={16} className="text-blue-600" />
                  ) : (
                    <Square size={16} className="text-gray-400" />
                  )}
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onRename(conv.id, conv.name);
                  }}
                  title="Rename conversation"
                  className="flex-shrink-0 p-1.5 text-gray-400 hover:text-green-600 hover:bg-green-50 dark:hover:bg-green-900/20 rounded transition"
                >
                  <Edit size={16} />
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    openDeleteModal(conv);
                  }}
                  title="Delete conversation"
                  className="flex-shrink-0 p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded transition"
                >
                  <Trash2 size={16} />
                </button>
              </div>
            </div>
          ))
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
