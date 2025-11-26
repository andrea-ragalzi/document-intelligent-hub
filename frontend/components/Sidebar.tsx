import { MessageSquarePlus, Search } from "lucide-react";
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
          aria-label="Close sidebar"
          className="fixed inset-0 bg-black/50 dark:bg-indigo-950/80 z-40 transition-opacity duration-300 lg:hidden"
          onClick={onClose}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " " || e.key === "Escape") {
              e.preventDefault();
              onClose();
            }
          }}
        />
      )}

      {/* Sidebar - Permanente su desktop (lg+), overlay su mobile */}
      <div
        className={`
          h-full w-72
          bg-indigo-50 dark:bg-indigo-950 
          shadow-lg
          transform transition-all duration-200 ease-in-out
          flex flex-col
          border-r-2 border-indigo-100 dark:border-indigo-800
          font-[Inter]
          
          lg:relative lg:translate-x-0 lg:z-0
          
          fixed top-0 left-0 z-50
          ${isOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"}
        `}
      >
        {/* Search & New Chat Section */}
        <div className="p-4 space-y-3 border-b-2 border-indigo-100 dark:border-indigo-800">
          {/* Search Input */}
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Search
                size={18}
                className="text-indigo-700 dark:text-indigo-200"
              />
            </div>
            <input
              type="text"
              placeholder="Search conversations..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-3 py-3 text-base bg-white dark:bg-indigo-900 border-2 border-indigo-300 dark:border-indigo-700 rounded-lg focus:outline-none focus:ring-3 focus:ring-focus focus:border-indigo-500 text-indigo-900 dark:text-indigo-50 placeholder-indigo-700 dark:placeholder-indigo-300 transition-colors"
            />
          </div>

          {/* New Chat Button */}
          <button
            onClick={(e) => {
              e.stopPropagation();
              e.preventDefault();
              console.log("🆕 New Chat button clicked");
              onNewConversation();
              onClose();
            }}
            className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-indigo-600 hover:bg-indigo-700 active:bg-indigo-800 dark:bg-indigo-600 dark:hover:bg-indigo-500 dark:active:bg-indigo-400 text-white rounded-lg transition-colors duration-150 font-medium text-base focus:outline-none focus:ring-3 focus:ring-focus min-h-[44px]"
          >
            <MessageSquarePlus size={20} />
            <span>New Chat</span>
          </button>
        </div>

        {/* Conversations List - Scrollable with strong contrast */}
        <div className="flex-1 overflow-y-auto px-3 py-4 bg-indigo-50 dark:bg-indigo-950">
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
