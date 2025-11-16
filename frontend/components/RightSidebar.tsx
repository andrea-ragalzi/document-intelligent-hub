"use client";

import {
  X,
  LogOut,
  Sun,
  Moon,
  FileText,
  ChevronRight,
  ChevronLeft,
} from "lucide-react";
import { useState, useEffect } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { useRouter } from "next/navigation";
import Image from "next/image";
import DocumentList from "./DocumentList";
import type { Document } from "./DocumentList";
import { AlertMessage } from "./AlertMessage";
import type { AlertState } from "@/lib/types";

interface RightSidebarProps {
  userId: string | null;
  theme: "light" | "dark";
  isOpen: boolean;
  onClose: () => void;
  onToggleTheme: () => void;
  documents: Document[];
  isLoadingDocuments?: boolean;
  statusAlert: AlertState | null;
  onDeleteDocument: (filename: string) => void;
  onRefreshDocuments?: () => Promise<void>;
}

export const RightSidebar: React.FC<RightSidebarProps> = ({
  userId,
  theme,
  isOpen,
  onClose,
  onToggleTheme,
  documents,
  statusAlert,
  onDeleteDocument,
}) => {
  const [activeView, setActiveView] = useState<"menu" | "documents">("menu");
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
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 transition-opacity duration-300"
          onClick={onClose}
        />
      )}
      <div
        className={`fixed top-0 right-0 h-full w-96 bg-white dark:bg-gray-800 shadow-2xl z-50 transform transition-transform duration-300 ease-in-out flex flex-col ${
          isOpen ? "translate-x-0" : "translate-x-full"
        }`}
      >
        {activeView === "documents" && (
          <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
            <button
              onClick={() => setActiveView("menu")}
              className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition"
            >
              <ChevronLeft
                size={22}
                className="text-gray-500 dark:text-gray-400"
              />
            </button>
            <h2 className="flex-1 text-center text-xl font-bold text-gray-900 dark:text-white">
              Documents
            </h2>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition"
            >
              <X size={22} className="text-gray-500 dark:text-gray-400" />
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
                <p className="text-sm font-semibold text-gray-900 dark:text-white truncate">
                  {displayName}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
                  {user?.email}
                </p>
              </div>
              <button
                onClick={onClose}
                className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition"
              >
                <X size={22} className="text-gray-500 dark:text-gray-400" />
              </button>
            </div>
            <div className="bg-gray-50 dark:bg-gray-900/50 rounded-lg p-3">
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
                onClick={() => setActiveView("documents")}
                className="w-full flex items-center justify-between px-4 py-3 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition text-left"
              >
                <div className="flex items-center gap-3">
                  <FileText
                    size={20}
                    className="text-gray-600 dark:text-gray-400"
                  />
                  <span className="text-sm font-medium text-gray-900 dark:text-white">
                    Gestione Documenti
                  </span>
                </div>
                <ChevronRight
                  size={22}
                  className="text-gray-500 dark:text-gray-400"
                />
              </button>
              <button
                onClick={onToggleTheme}
                className="w-full flex items-center justify-between px-4 py-3 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition text-left"
              >
                <div className="flex items-center gap-3">
                  <ThemeIcon
                    size={20}
                    className="text-gray-600 dark:text-gray-400"
                  />
                  <span className="text-sm font-medium text-gray-900 dark:text-white">
                    Tema
                  </span>
                </div>
                <span className="text-xs text-gray-500 dark:text-gray-400 capitalize">
                  {theme}
                </span>
              </button>
            </div>
          ) : (
            <div className="p-4 space-y-4">
              {statusAlert && <AlertMessage alert={statusAlert} />}
              <DocumentList
                documents={documents}
                deletingDoc={null}
                onDelete={onDeleteDocument}
              />
            </div>
          )}
        </div>
        <div className="p-4 border-t border-gray-200 dark:border-gray-700">
          <button
            onClick={handleLogout}
            className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-red-600 hover:bg-red-700 text-white rounded-lg transition font-medium"
          >
            <LogOut size={18} />
            Logout
          </button>
        </div>
      </div>
    </>
  );
};
