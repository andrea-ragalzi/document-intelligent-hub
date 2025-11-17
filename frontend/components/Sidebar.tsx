import { PlusCircle, Search } from "lucide-react";
import { useEffect, useState } from "react";
import { ConversationList } from "./ConversationList";
import type { SavedConversation } from "@/lib/types";

interface SidebarProps {
  userId: string | null;
  savedConversations: SavedConversation[];
  currentConversationId?: string | null;
  isOpen: boolean;
  onClose: () => void;
  onNewConversation: () => void;
  onLoadConversation: (conv: SavedConversation) => void;
  onDeleteConversation: (id: string, name: string) => void;
  onRenameConversation: (id: string, currentName: string) => void;
  onPinConversation: (id: string, isPinned: boolean) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  savedConversations,
  currentConversationId,
  isOpen,
  onClose,
  onNewConversation,
  onLoadConversation,
  onDeleteConversation,
  onRenameConversation,
  onPinConversation,
}) => {
  const [searchQuery, setSearchQuery] = useState("");

  // Filter conversations based on search query
  const filteredConversations = savedConversations.filter((conv) =>
    conv.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Close on escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) onClose();
    };

    document.addEventListener("keydown", handleEscape);
    return () => document.removeEventListener("keydown", handleEscape);
  }, [isOpen, onClose]);

  // Prevent body scroll when open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "unset";
    }

    return () => {
      document.body.style.overflow = "unset";
    };
  }, [isOpen]);

  return (
    <>
      {/* Overlay - Solo su mobile quando isOpen */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 transition-opacity duration-300 lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar - Permanente su desktop (lg+), overlay su mobile */}
      <div
        className={`
          h-full w-72
          bg-white dark:bg-gray-800 
          shadow-lg
          transform transition-all duration-200 ease-in-out
          flex flex-col
          border-r-2 border-gray-200 dark:border-gray-700
          font-[Inter]
          
          lg:relative lg:translate-x-0 lg:z-0
          
          fixed top-0 left-0 z-50
          ${isOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"}
        `}
      >
        {/* Search Input - Flat Design */}
        <div className="p-4 border-b-2 border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900">
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Search size={18} className="text-gray-400 dark:text-gray-500" />
            </div>
            <input
              type="text"
              placeholder="Search conversations..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-3 py-3 text-base bg-white dark:bg-gray-800 border-2 border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-gray-900 dark:text-gray-100 placeholder-gray-500 dark:placeholder-gray-400 transition-colors"
            />
          </div>
        </div>

        {/* New Chat Button - Flat Primary */}
        <div className="p-4 bg-gray-50 dark:bg-gray-900 border-b-2 border-gray-200 dark:border-gray-700 flex gap-2">
          <button
            onClick={(e) => {
              e.stopPropagation();
              e.preventDefault();
              console.log("🆕 New Chat button clicked");
              onNewConversation();
              onClose();
            }}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-indigo-600 hover:bg-indigo-700 active:bg-indigo-800 text-white rounded-lg transition-all duration-200 ease-in-out font-semibold text-base shadow-md hover:shadow-lg"
          >
            <PlusCircle size={20} />
            <span>New Chat</span>
          </button>
        </div>

        {/* Conversations List - Scrollable with strong contrast */}
        <div className="flex-1 overflow-y-auto px-3 py-4 bg-white dark:bg-gray-800">
          <ConversationList
            conversations={filteredConversations}
            currentConversationId={currentConversationId}
            onLoad={(conv) => {
              onLoadConversation(conv);
              onClose();
            }}
            onDelete={onDeleteConversation}
            onRename={onRenameConversation}
            onPin={onPinConversation}
          />
        </div>
      </div>
    </>
  );
};
