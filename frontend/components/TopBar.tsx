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
  onOpenRightSidebar,
}) => {
  return (
    <div className="w-full bg-indigo-50 dark:bg-indigo-950 border-b-2 border-indigo-100 dark:border-indigo-800 shadow-sm transition-colors duration-200 ease-in-out font-[Inter]">
      <div className="flex items-center justify-between px-4 py-3">
        {/* Left: Hamburger Menu - Solo mobile (nascosto su lg+) */}
        <button
          onClick={onOpenLeftSidebar}
          className="h-11 w-11 flex items-center justify-center rounded-lg hover:bg-indigo-100 dark:hover:bg-indigo-800 transition-all duration-200 ease-in-out text-indigo-900 dark:text-indigo-50 lg:hidden focus:outline-none focus:ring-3 focus:ring-focus"
          aria-label="Toggle navigation"
          title="Conversazioni"
        >
          <Menu size={20} />
        </button>

        {/* Spacer per desktop quando menu è nascosto */}
        <div className="hidden lg:block w-10"></div>

        {/* Center: Title */}
        <div className="flex-1 flex items-center justify-center gap-3">
          <h1 className="text-xl font-bold text-indigo-900 dark:text-indigo-50">
            Document Intelligent Hub
          </h1>
        </div>

        {/* Right: User Profile Icon - Solo mobile (nascosto su xl+) */}
        <button
          onClick={onOpenRightSidebar}
          className="h-11 w-11 flex items-center justify-center rounded-lg hover:bg-indigo-100 dark:hover:bg-indigo-800 transition-all duration-200 ease-in-out text-indigo-900 dark:text-indigo-50 xl:hidden focus:outline-none focus:ring-3 focus:ring-focus"
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
