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
          className="fixed inset-0 bg-black/50 dark:bg-indigo-950/80 z-40 transition-opacity duration-300 xl:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar - Permanente su desktop (xl+), overlay su mobile */}
      <div
        className={`h-full w-96 bg-indigo-50 dark:bg-indigo-950 shadow-xl transform transition-all duration-200 ease-in-out flex flex-col border-l-2 border-indigo-100 dark:border-indigo-800 font-[Inter]
          
          xl:relative xl:translate-x-0 xl:z-0
          
          fixed top-0 right-0 z-50
          ${isOpen ? "translate-x-0" : "translate-x-full xl:translate-x-0"}
        `}
      >
        {activeView === "documents" && (
          <div className="flex items-center justify-between p-4 border-b-2 border-indigo-100 dark:border-indigo-800 gap-2">
            <button
              onClick={() => setActiveView("menu")}
              className="flex items-center gap-2 text-base text-indigo-700 dark:text-indigo-200 hover:text-indigo-900 dark:hover:text-indigo-100 transition-all duration-200 ease-in-out h-11 w-11 justify-center rounded-lg hover:bg-indigo-100 dark:hover:bg-indigo-800 focus:outline-none focus:ring-3 focus:ring-focus"
            >
              <ChevronLeft
                size={20}
                className="text-indigo-700 dark:text-indigo-200"
              />
            </button>
            <h2 className="flex-1 text-center text-xl font-bold text-indigo-900 dark:text-indigo-50">
              Documents
            </h2>
            <button
              onClick={onClose}
              className="h-11 w-11 flex items-center justify-center rounded-lg hover:bg-indigo-100 dark:hover:bg-indigo-800 transition-all duration-200 ease-in-out xl:hidden focus:outline-none focus:ring-3 focus:ring-focus"
            >
              <X size={20} className="text-indigo-700 dark:text-indigo-200" />
            </button>
          </div>
        )}
        {activeView === "settings" && (
          <div className="flex items-center justify-between p-4 border-b-2 border-indigo-100 dark:border-indigo-800 gap-2">
            <button
              onClick={() => setActiveView("menu")}
              className="flex items-center gap-2 text-base text-indigo-700 dark:text-indigo-200 hover:text-indigo-900 dark:hover:text-indigo-100 transition-all duration-200 ease-in-out h-11 w-11 justify-center rounded-lg hover:bg-indigo-100 dark:hover:bg-indigo-800 focus:outline-none focus:ring-3 focus:ring-focus"
            >
              <ChevronLeft
                size={20}
                className="text-indigo-700 dark:text-indigo-200"
              />
            </button>
            <h2 className="flex-1 text-center text-xl font-bold text-indigo-900 dark:text-indigo-50">
              Settings
            </h2>
            <button
              onClick={onClose}
              className="h-11 w-11 flex items-center justify-center rounded-lg hover:bg-indigo-100 dark:hover:bg-indigo-800 transition-all duration-200 ease-in-out xl:hidden focus:outline-none focus:ring-3 focus:ring-focus"
            >
              <X size={20} className="text-indigo-700 dark:text-indigo-200" />
            </button>
          </div>
        )}
        {activeView === "menu" && (
          <div className="px-6 py-4 border-b border-indigo-100 dark:border-indigo-800">
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
                <div className="w-12 h-12 rounded-full bg-indigo-500 flex items-center justify-center text-white font-medium text-lg">
                  {displayName[0]?.toUpperCase() || "U"}
                </div>
              )}
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-indigo-900 dark:text-indigo-50 truncate">
                  {displayName}
                </p>
                <p className="text-xs text-indigo-700 dark:text-indigo-200 truncate">
                  {user?.email}
                </p>
              </div>
              <button
                onClick={onClose}
                className="h-11 w-11 flex items-center justify-center rounded-lg hover:bg-indigo-100 dark:hover:bg-indigo-800 transition-all duration-200 ease-in-out xl:hidden focus:outline-none focus:ring-3 focus:ring-focus"
              >
                <X size={20} className="text-indigo-700 dark:text-indigo-200" />
              </button>
            </div>
            <div className="bg-indigo-100 dark:bg-indigo-900 rounded-lg p-3 mb-3">
              <p className="text-xs text-indigo-700 dark:text-indigo-200 mb-1">
                User ID
              </p>
              <p className="text-xs font-mono text-indigo-900 dark:text-indigo-50 break-all">
                {userId || "Non disponibile"}
              </p>
            </div>

            {/* Logout button - Gemini style */}
            <button
              onClick={handleLogout}
              className="min-h-[44px] w-full flex items-center justify-center gap-2 px-4 py-2 text-sm font-medium text-indigo-900 dark:text-indigo-50 border-2 border-indigo-300 dark:border-indigo-700 hover:bg-indigo-100 dark:hover:bg-indigo-800 rounded-lg transition-all duration-200 focus:outline-none focus:ring-3 focus:ring-focus"
            >
              <LogOut size={16} />
              Logout
            </button>
          </div>
        )}
        <div className="flex-1 overflow-y-auto">
          {activeView === "menu" ? (
            <div className="p-4 space-y-2">
              <button
                onClick={onToggleTheme}
                className="min-h-[44px] w-full flex items-center justify-between px-4 py-3 rounded-lg hover:bg-indigo-100 dark:hover:bg-indigo-800 transition-all duration-200 ease-in-out text-left focus:outline-none focus:ring-3 focus:ring-focus"
              >
                <div className="flex items-center gap-3">
                  <ThemeIcon
                    size={20}
                    className="text-indigo-700 dark:text-indigo-200"
                  />
                  <span className="text-base font-medium text-indigo-900 dark:text-indigo-50">
                    Tema
                  </span>
                </div>
                <span className="text-sm text-indigo-700 dark:text-indigo-200 capitalize">
                  {theme}
                </span>
              </button>
              <button
                onClick={() => setActiveView("documents")}
                className="min-h-[44px] w-full flex items-center justify-between px-4 py-3 rounded-lg hover:bg-indigo-100 dark:hover:bg-indigo-800 transition-all duration-200 ease-in-out text-left focus:outline-none focus:ring-3 focus:ring-focus"
              >
                <div className="flex items-center gap-3">
                  <FileText
                    size={20}
                    className="text-indigo-700 dark:text-indigo-200"
                  />
                  <span className="text-base font-medium text-indigo-900 dark:text-indigo-50">
                    Gestione Documenti
                  </span>
                </div>
                <ChevronRight
                  size={20}
                  className="text-indigo-700 dark:text-indigo-200"
                />
              </button>
              <button
                onClick={() => setActiveView("settings")}
                className="min-h-[44px] w-full flex items-center justify-between px-4 py-3 rounded-lg hover:bg-indigo-100 dark:hover:bg-indigo-800 transition-all duration-200 ease-in-out text-left focus:outline-none focus:ring-3 focus:ring-focus"
              >
                <div className="flex items-center gap-3">
                  <Settings
                    size={20}
                    className="text-indigo-700 dark:text-indigo-200"
                  />
                  <span className="text-base font-medium text-indigo-900 dark:text-indigo-50">
                    Settings
                  </span>
                </div>
                <ChevronRight
                  size={20}
                  className="text-indigo-700 dark:text-indigo-200"
                />
              </button>
            </div>
          ) : activeView === "settings" ? (
            <div className="p-4">
              <div className="border-2 border-indigo-300 dark:border-indigo-700 rounded-lg p-4">
                <h3 className="text-base font-semibold text-indigo-900 dark:text-indigo-50 mb-2">
                  Account Management
                </h3>
                <p className="text-sm text-indigo-700 dark:text-indigo-200 mb-4">
                  Permanently delete your account and all associated data. This
                  action cannot be undone.
                </p>
                <button
                  onClick={onDeleteAccount}
                  className="min-h-[44px] w-full px-4 py-2 text-sm font-medium text-red-700 dark:text-red-400 border-2 border-red-300 dark:border-red-800 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors focus:outline-none focus:ring-3 focus:ring-focus"
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
      </div>
    </>
  );
};
