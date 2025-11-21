"use client";

import {
  X,
  LogOut,
  Sun,
  Moon,
  FileText,
  ChevronRight,
  ChevronLeft,
  Settings,
} from "lucide-react";
import { useState, useEffect } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { useRouter } from "next/navigation";
import Image from "next/image";
import DocumentList from "./DocumentList";
import type { Document } from "./DocumentList";

interface RightSidebarProps {
  userId: string | null;
  theme: "light" | "dark";
  isOpen: boolean;
  onClose: () => void;
  onToggleTheme: () => void;
  documents: Document[];
  isLoadingDocuments?: boolean;
  onDeleteDocument: (filename: string) => void;
  onRefreshDocuments?: () => Promise<void>;
  onDeleteAccount: () => void;
}

export const RightSidebar: React.FC<RightSidebarProps> = ({
  userId,
  theme,
  isOpen,
  onClose,
  onToggleTheme,
  documents,
  onDeleteDocument,
  onDeleteAccount,
}) => {
  const [activeView, setActiveView] = useState<
    "menu" | "documents" | "settings"
  >("menu");
  const { user, logout } = useAuth();
  const router = useRouter();

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) onClose();
    };
    document.addEventListener("keydown", handleEscape);
    return () => document.removeEventListener("keydown", handleEscape);
  }, [isOpen, onClose]);

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

  const handleLogout = async () => {
    try {
      await logout();
      router.push("/login");
    } catch (error) {
      console.error("Failed to logout:", error);
    }
  };

  const displayName = user?.displayName || user?.email || "Utente";
  const ThemeIcon = theme === "light" ? Moon : Sun;

  return (
    <>
      {/* Overlay - Solo su mobile quando isOpen */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 transition-opacity duration-300 xl:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar - Permanente su desktop (xl+), overlay su mobile */}
      <div
        className={`h-full w-96 bg-gray-50 dark:bg-gray-900 shadow-xl transform transition-all duration-200 ease-in-out flex flex-col border-l-2 border-gray-200 dark:border-gray-700 font-[Inter]
          
          xl:relative xl:translate-x-0 xl:z-0
          
          fixed top-0 right-0 z-50
          ${isOpen ? "translate-x-0" : "translate-x-full xl:translate-x-0"}
        `}
      >
        {activeView === "documents" && (
          <div className="flex items-center justify-between p-4 border-b-2 border-gray-200 dark:border-gray-700 gap-2">
            <button
              onClick={() => setActiveView("menu")}
              className="flex items-center gap-2 text-base text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-all duration-200 ease-in-out h-10 w-10 justify-center rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800"
            >
              <ChevronLeft
                size={20}
                className="text-gray-500 dark:text-gray-400"
              />
            </button>
            <h2 className="flex-1 text-center text-xl font-bold text-gray-900 dark:text-gray-100">
              Documents
            </h2>
            <button
              onClick={onClose}
              className="h-10 w-10 flex items-center justify-center rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-all duration-200 ease-in-out xl:hidden"
            >
              <X size={20} className="text-gray-500 dark:text-gray-400" />
            </button>
          </div>
        )}
        {activeView === "settings" && (
          <div className="flex items-center justify-between p-4 border-b-2 border-gray-200 dark:border-gray-700 gap-2">
            <button
              onClick={() => setActiveView("menu")}
              className="flex items-center gap-2 text-base text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-all duration-200 ease-in-out h-10 w-10 justify-center rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800"
            >
              <ChevronLeft
                size={20}
                className="text-gray-500 dark:text-gray-400"
              />
            </button>
            <h2 className="flex-1 text-center text-xl font-bold text-gray-900 dark:text-gray-100">
              Settings
            </h2>
            <button
              onClick={onClose}
              className="h-10 w-10 flex items-center justify-center rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-all duration-200 ease-in-out xl:hidden"
            >
              <X size={20} className="text-gray-500 dark:text-gray-400" />
            </button>
          </div>
        )}
        {activeView === "menu" && (
          <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-3 mb-3">
              {user?.photoURL ? (
                <Image
                  src={user.photoURL}
                  alt="Profile"
                  width={48}
                  height={48}
                  className="rounded-full"
                />
              ) : (
                <div className="w-12 h-12 rounded-full bg-blue-600 flex items-center justify-center text-white font-medium text-lg">
                  {displayName[0]?.toUpperCase() || "U"}
                </div>
              )}
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-gray-900 dark:text-gray-100 truncate">
                  {displayName}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
                  {user?.email}
                </p>
              </div>
              <button
                onClick={onClose}
                className="h-10 w-10 flex items-center justify-center rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-all duration-200 ease-in-out xl:hidden"
              >
                <X size={20} className="text-gray-500 dark:text-gray-400" />
              </button>
            </div>
            <div className="bg-gray-100 dark:bg-gray-800 rounded-lg p-3">
              <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">
                User ID
              </p>
              <p className="text-xs font-mono text-gray-700 dark:text-gray-300 break-all">
                {userId || "Non disponibile"}
              </p>
            </div>
          </div>
        )}
        <div className="flex-1 overflow-y-auto">
          {activeView === "menu" ? (
            <div className="p-4 space-y-2">
              <button
                onClick={onToggleTheme}
                className="w-full flex items-center justify-between px-4 py-3 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-all duration-200 ease-in-out text-left"
              >
                <div className="flex items-center gap-3">
                  <ThemeIcon
                    size={20}
                    className="text-gray-600 dark:text-gray-400"
                  />
                  <span className="text-base font-medium text-gray-900 dark:text-gray-100">
                    Tema
                  </span>
                </div>
                <span className="text-sm text-gray-500 dark:text-gray-400 capitalize">
                  {theme}
                </span>
              </button>
              <button
                onClick={() => setActiveView("documents")}
                className="w-full flex items-center justify-between px-4 py-3 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-all duration-200 ease-in-out text-left"
              >
                <div className="flex items-center gap-3">
                  <FileText
                    size={20}
                    className="text-gray-600 dark:text-gray-400"
                  />
                  <span className="text-base font-medium text-gray-900 dark:text-gray-100">
                    Gestione Documenti
                  </span>
                </div>
                <ChevronRight
                  size={20}
                  className="text-gray-500 dark:text-gray-400"
                />
              </button>
              <button
                onClick={() => setActiveView("settings")}
                className="w-full flex items-center justify-between px-4 py-3 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-all duration-200 ease-in-out text-left"
              >
                <div className="flex items-center gap-3">
                  <Settings
                    size={20}
                    className="text-gray-600 dark:text-gray-400"
                  />
                  <span className="text-base font-medium text-gray-900 dark:text-gray-100">
                    Settings
                  </span>
                </div>
                <ChevronRight
                  size={20}
                  className="text-gray-500 dark:text-gray-400"
                />
              </button>
            </div>
          ) : activeView === "settings" ? (
            <div className="p-4">
              <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                <h3 className="text-base font-semibold text-gray-900 dark:text-gray-100 mb-2">
                  Account Management
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                  Permanently delete your account and all associated data. This action cannot be undone.
                </p>
                <button
                  onClick={onDeleteAccount}
                  className="w-full px-4 py-2 text-sm font-medium text-red-700 dark:text-red-400 border border-red-300 dark:border-red-800 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                >
                  Delete Account
                </button>
              </div>
            </div>
          ) : (
            <div className="p-4 flex-1 flex flex-col overflow-hidden">
              <DocumentList
                documents={documents}
                deletingDoc={null}
                onDelete={onDeleteDocument}
              />
            </div>
          )}
        </div>

        {/* Logout button - only visible in menu view */}
        {activeView === "menu" && (
          <div className="p-4 border-t border-gray-200 dark:border-gray-700">
            <button
              onClick={handleLogout}
              className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-all duration-200 ease-in-out font-semibold text-base shadow-md hover:shadow-lg"
            >
              <LogOut size={18} />
              Logout
            </button>
          </div>
        )}
      </div>
    </>
  );
};
