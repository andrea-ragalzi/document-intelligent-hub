import { PlusCircle, Search } from "lucide-react";
import { useEffect, useState } from "react";
import { ConversationList } from "./ConversationList";
import type { SavedConversation } from "@/lib/types";

interface SidebarProps {
  userId: string | null;
  savedConversations: SavedConversation[];
  isOpen: boolean;
  onClose: () => void;
  onNewConversation: () => void;
  onLoadConversation: (conv: SavedConversation) => void;
  onDeleteConversation: (id: string, name: string) => void;
  onRenameConversation: (id: string, currentName: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  savedConversations,
  isOpen,
  onClose,
  onNewConversation,
  onLoadConversation,
  onDeleteConversation,
  onRenameConversation,
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
      {/* Overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 transition-opacity duration-300"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <div
        className={`
          fixed top-0 left-0 h-full w-64
          bg-white dark:bg-gray-800 
          shadow-2xl z-50
          transform transition-transform duration-300 ease-in-out
          flex flex-col
          ${isOpen ? "translate-x-0" : "-translate-x-full"}
        `}
      >
        {/* Search Input */}
        <div className="p-4">
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Search size={16} className="text-gray-400 dark:text-gray-500" />
            </div>
            <input
              type="text"
              placeholder="Search conversations..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-2.5 text-sm bg-gray-100 dark:bg-gray-700 border-0 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white dark:focus:bg-gray-600 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 transition-colors"
            />
          </div>
        </div>

        {/* New Chat Button */}
        <div className="px-4 pb-4">
          <button
            onClick={(e) => {
              e.stopPropagation();
              e.preventDefault();
              console.log("🆕 New Chat button clicked");
              onNewConversation();
              onClose();
            }}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white rounded-lg transition-all duration-200 font-medium shadow-sm hover:shadow-md"
          >
            <PlusCircle size={18} />
            <span className="text-sm">New Chat</span>
          </button>
        </div>

        {/* Conversations List - Scrollable */}
        <div className="flex-1 overflow-y-auto px-4 pb-4">
          <ConversationList
            conversations={filteredConversations}
            onLoad={(conv) => {
              onLoadConversation(conv);
              onClose();
            }}
            onDelete={onDeleteConversation}
            onRename={onRenameConversation}
          />
        </div>
      </div>
    </>
  );
};
