"use client";

import { Menu, User, PlusCircle } from "lucide-react";

interface TopBarProps {
  onOpenLeftSidebar: () => void;
  onOpenRightSidebar: () => void;
  onNewConversation: () => void;
  hasConversation: boolean;
}

export const TopBar: React.FC<TopBarProps> = ({
  onOpenLeftSidebar,
  onOpenRightSidebar,
  onNewConversation,
  hasConversation,
}) => {
  return (
    <div className="w-full bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 shadow-sm transition-colors duration-300">
      <div className="flex items-center justify-between px-4 py-3">
        {/* Left: Hamburger Menu - Always visible */}
        <button
          onClick={onOpenLeftSidebar}
          className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition text-gray-700 dark:text-gray-300"
          aria-label="Toggle navigation"
          title="Conversazioni"
        >
          <Menu size={22} />
        </button>

        {/* Center: Title and New Chat Button */}
        <div className="flex-1 flex items-center justify-center gap-3">
          <h1 className="text-lg font-bold text-gray-900 dark:text-white">
            Document RAG
          </h1>
          <button
            onClick={onNewConversation}
            disabled={!hasConversation}
            title="Nuova conversazione"
            className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition text-sm font-medium"
          >
            <PlusCircle size={16} />
            Nuova Chat
          </button>
        </div>

        {/* Right: User Profile Icon - Always visible */}
        <button
          onClick={onOpenRightSidebar}
          className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition text-gray-700 dark:text-gray-300"
          aria-label="Toggle settings"
          title="Impostazioni"
        >
          <User size={22} />
        </button>
      </div>
    </div>
  );
};
