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
  const filteredConversations = savedConversations.filter(conv =>
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
          aria-hidden="true"
          className="fixed inset-0 bg-black/55 z-40 transition-opacity duration-300 lg:hidden"
          onClick={onClose}
          onKeyDown={e => {
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
          bg-raised
          transform transition-all duration-200 ease-in-out
          flex flex-col
          border-r border-line/15
          font-[Inter]

          lg:relative lg:translate-x-0 lg:z-0

          fixed top-0 left-0 z-50
          ${isOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"}
        `}
      >
        {/* Search & New Chat Section */}
        <div className="p-4 space-y-3 border-b border-line/15">
          {/* Search Input */}
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Search size={18} className="text-quiet" />
            </div>
            <input
              type="text"
              placeholder="Search conversations..."
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              className="ui-input w-full pl-10 pr-3 py-3 text-base rounded-lg focus:outline-none focus:ring-0 transition-colors"
            />
          </div>

          {/* New Chat Button */}
          <button
            onClick={e => {
              e.stopPropagation();
              e.preventDefault();
              onNewConversation();
              onClose();
            }}
            className="ui-primary-action w-full flex items-center justify-center gap-2 px-4 py-3 rounded-lg transition-colors duration-150 font-medium text-base focus:outline-none focus:ring-3 focus:ring-focus min-h-[44px]"
          >
            <MessageSquarePlus size={20} />
            <span>New Chat</span>
          </button>
        </div>

        {/* Conversations List - Scrollable with strong contrast */}
        <div className="flex-1 overflow-y-auto px-3 py-4">
          <ConversationList
            conversations={filteredConversations}
            currentConversationId={currentConversationId}
            onLoad={conv => {
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
