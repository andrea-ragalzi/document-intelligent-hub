"use client";

import { Menu, User } from "lucide-react";

interface TopBarProps {
  onOpenLeftSidebar: () => void;
  onOpenRightSidebar: () => void;
  onNewConversation: () => void;
  hasConversation: boolean;
}

export const TopBar: React.FC<TopBarProps> = ({
  onOpenLeftSidebar,
  onOpenRightSidebar
}) => {
  return (
    <div className="w-full bg-white dark:bg-gray-900 border-b-2 border-gray-200 dark:border-gray-700 shadow-sm transition-colors duration-200 ease-in-out font-[Inter]">
      <div className="flex items-center justify-between px-4 py-3">
        {/* Left: Hamburger Menu - Solo mobile (nascosto su lg+) */}
        <button
          onClick={onOpenLeftSidebar}
          className="h-10 w-10 flex items-center justify-center rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-all duration-200 ease-in-out text-gray-700 dark:text-gray-300 lg:hidden"
          aria-label="Toggle navigation"
          title="Conversazioni"
        >
          <Menu size={20} />
        </button>

        {/* Spacer per desktop quando menu è nascosto */}
        <div className="hidden lg:block w-10"></div>

        {/* Center: Title */}
        <div className="flex-1 flex items-center justify-center gap-3">
          <h1 className="text-lg font-bold text-gray-900 dark:text-gray-100">
            Document Intelligent Hub
          </h1>
        </div>

        {/* Right: User Profile Icon - Solo mobile (nascosto su xl+) */}
        <button
          onClick={onOpenRightSidebar}
          className="h-10 w-10 flex items-center justify-center rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-all duration-200 ease-in-out text-gray-700 dark:text-gray-300 xl:hidden"
          aria-label="Toggle settings"
          title="Impostazioni"
        >
          <User size={20} />
        </button>

        {/* Spacer per desktop quando menu è nascosto */}
        <div className="hidden xl:block w-10"></div>
      </div>
    </div>
  );
};
