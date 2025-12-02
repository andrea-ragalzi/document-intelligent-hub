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
  Bug,
  Star,
  Info,
} from "lucide-react";
import { useState, useEffect } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { useRouter } from "next/navigation";
import Image from "next/image";
import DocumentList from "./DocumentList";
import TierLimitsDisplay from "./TierLimitsDisplay";
import type { Document } from "./DocumentList";
import { SettingsView } from "./RightSidebar/SettingsView";
import { DocumentsView } from "./RightSidebar/DocumentsView";
import { SidebarHeader } from "./RightSidebar/SidebarHeader";
import { MenuProfileSection } from "./RightSidebar/MenuProfileSection";

interface RightSidebarProps {
  userId: string | null;
  theme: "light" | "dark";
  isOpen: boolean;
  onClose: () => void;
  onToggleTheme: () => void;
  documents: Document[] | undefined;
  isLoadingDocuments?: boolean;
  onDeleteDocument: (filename: string) => void;
  onRefreshDocuments?: () => Promise<void>;
  onDeleteAccount: () => void;
  onOpenBugReport: () => void;
  onOpenFeedback: () => void;
  isServerOnline?: boolean;
  currentQueries?: number;
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
  onOpenBugReport,
  onOpenFeedback,
  isServerOnline = true,
  currentQueries = 0,
}) => {
  const [activeView, setActiveView] = useState<"menu" | "documents" | "settings">("menu");
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
          aria-hidden="true"
          className="fixed inset-0 bg-black/50 dark:bg-indigo-950/80 z-40 transition-opacity duration-300 xl:hidden"
          onClick={onClose}
          onKeyDown={e => e.key === "Escape" && onClose()}
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
        <SidebarHeader
          activeView={activeView}
          onClose={onClose}
          onBackToMenu={() => setActiveView("menu")}
        />
        {activeView === "menu" && (
          <MenuProfileSection
            user={user}
            userId={userId}
            displayName={displayName}
            documents={documents}
            currentQueries={currentQueries}
            onClose={onClose}
            onLogout={handleLogout}
          />
        )}
        <div className="flex-1 overflow-y-auto">
          {activeView === "menu" ? (
            <div className="p-4 space-y-2">
              <button
                onClick={onToggleTheme}
                className="min-h-[44px] w-full flex items-center justify-between px-4 py-3 rounded-lg hover:bg-indigo-100 dark:hover:bg-indigo-800 transition-all duration-200 ease-in-out text-left focus:outline-none focus:ring-3 focus:ring-focus"
              >
                <div className="flex items-center gap-3">
                  <ThemeIcon size={20} className="text-indigo-700 dark:text-indigo-200" />
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
                  <FileText size={20} className="text-indigo-700 dark:text-indigo-200" />
                  <span className="text-base font-medium text-indigo-900 dark:text-indigo-50">
                    Gestione Documenti
                  </span>
                </div>
                <ChevronRight size={20} className="text-indigo-700 dark:text-indigo-200" />
              </button>
              <button
                onClick={() => setActiveView("settings")}
                className="min-h-[44px] w-full flex items-center justify-between px-4 py-3 rounded-lg hover:bg-indigo-100 dark:hover:bg-indigo-800 transition-all duration-200 ease-in-out text-left focus:outline-none focus:ring-3 focus:ring-focus"
              >
                <div className="flex items-center gap-3">
                  <Settings size={20} className="text-indigo-700 dark:text-indigo-200" />
                  <span className="text-base font-medium text-indigo-900 dark:text-indigo-50">
                    Settings
                  </span>
                </div>
                <ChevronRight size={20} className="text-indigo-700 dark:text-indigo-200" />
              </button>
              <button
                onClick={() => {
                  onOpenBugReport();
                  onClose();
                }}
                className="min-h-[44px] w-full flex items-center justify-between px-4 py-3 rounded-lg hover:bg-indigo-100 dark:hover:bg-indigo-800 transition-all duration-200 ease-in-out text-left focus:outline-none focus:ring-3 focus:ring-focus"
              >
                <div className="flex items-center gap-3">
                  <Bug size={20} className="text-red-600 dark:text-red-400" />
                  <span className="text-base font-medium text-indigo-900 dark:text-indigo-50">
                    Report Bug
                  </span>
                </div>
              </button>
              <button
                onClick={() => {
                  onOpenFeedback();
                  onClose();
                }}
                className="min-h-[44px] w-full flex items-center justify-between px-4 py-3 rounded-lg hover:bg-indigo-100 dark:hover:bg-indigo-800 transition-all duration-200 ease-in-out text-left focus:outline-none focus:ring-3 focus:ring-focus"
              >
                <div className="flex items-center gap-3">
                  <Star size={20} className="text-yellow-600 dark:text-yellow-400" />
                  <span className="text-base font-medium text-indigo-900 dark:text-indigo-50">
                    Give Feedback
                  </span>
                </div>
              </button>
              <button
                onClick={() => {
                  router.push("/about");
                  onClose();
                }}
                className="min-h-[44px] w-full flex items-center justify-between px-4 py-3 rounded-lg hover:bg-indigo-100 dark:hover:bg-indigo-800 transition-all duration-200 ease-in-out text-left focus:outline-none focus:ring-3 focus:ring-focus"
              >
                <div className="flex items-center gap-3">
                  <Info size={20} className="text-indigo-600 dark:text-indigo-300" />
                  <span className="text-base font-medium text-indigo-900 dark:text-indigo-50">
                    About
                  </span>
                </div>
              </button>
            </div>
          ) : activeView === "settings" ? (
            <SettingsView onDeleteAccount={onDeleteAccount} />
          ) : activeView === "documents" ? (
            <DocumentsView
              documents={documents}
              onDeleteDocument={onDeleteDocument}
              isServerOnline={isServerOnline}
            />
          ) : null}
        </div>
      </div>
    </>
  );
};
