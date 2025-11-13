"use client";

import { Menu, User, PlusCircle } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import Image from "next/image";

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
  const { user } = useAuth();

  return (
    <div className="flex-shrink-0 w-full z-50 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 transition-colors duration-300">
      <div className="flex items-center justify-between px-3 py-2 sm:px-4 sm:py-3">
        {/* Left: Hamburger Menu */}
        <button
          onClick={onOpenLeftSidebar}
          className="lg:hidden p-2 rounded-lg bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 transition text-gray-700 dark:text-gray-300"
          aria-label="Open menu"
        >
          <Menu size={20} />
        </button>

        {/* Center: Title and New Chat Button */}
        <div className="flex-1 flex items-center justify-center gap-3 lg:justify-start lg:ml-4">
          <h1 className="text-base sm:text-lg font-bold text-gray-900 dark:text-white">
            Document RAG
          </h1>
          <button
            onClick={onNewConversation}
            disabled={!hasConversation}
            title="New conversation"
            className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition text-sm font-medium"
          >
            <PlusCircle size={16} />
            New Chat
          </button>
        </div>

        {/* Right: Profile Button */}
        <button
          onClick={onOpenRightSidebar}
          className="lg:hidden p-1.5 rounded-lg bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 transition"
          aria-label="Open profile"
        >
          {user ? (
            user.photoURL ? (
              <Image
                src={user.photoURL}
                alt="Profile"
                width={28}
                height={28}
                className="rounded-full"
              />
            ) : (
              <div className="w-7 h-7 rounded-full bg-blue-600 flex items-center justify-center text-white text-xs font-medium">
                {user.email?.[0].toUpperCase() || "?"}
              </div>
            )
          ) : (
            <div className="w-7 h-7 rounded-full bg-gray-400 flex items-center justify-center text-white">
              <User size={16} />
            </div>
          )}
        </button>
      </div>
    </div>
  );
};
