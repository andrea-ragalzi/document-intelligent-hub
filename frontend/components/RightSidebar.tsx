"use client";

import {
  User,
  ChevronLeft,
  ChevronRight,
  LogOut,
  Sun,
  Moon,
  RefreshCw,
  FileText,
} from "lucide-react";
import { useState, useEffect } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { useRouter } from "next/navigation";
import Image from "next/image";
import { DocumentList, Document } from "./DocumentList";
import { AlertMessage } from "./AlertMessage";
import type { AlertState } from "@/lib/types";

interface RightSidebarProps {
  userId: string | null;
  theme: "light" | "dark";
  mobileOpen: boolean;
  onCloseMobile: () => void;
  onToggleTheme: () => void;
  // Document management props
  documents: Document[];
  isLoadingDocuments: boolean;
  statusAlert: AlertState | null;
  onDeleteDocument: (filename: string) => void;
  onRefreshDocuments: () => void;
}

export const RightSidebar: React.FC<RightSidebarProps> = ({
  userId,
  theme,
  mobileOpen,
  onCloseMobile,
  onToggleTheme,
  documents,
  isLoadingDocuments,
  statusAlert,
  onDeleteDocument,
  onRefreshDocuments,
}) => {
  const [collapsed, setCollapsed] = useState(false);
  const [activeTab, setActiveTab] = useState<"account" | "documents">("account");
  const { user, logout } = useAuth();
  const router = useRouter();

  // Close mobile menu when clicking outside or on escape
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") onCloseMobile();
    };

    if (mobileOpen) {
      document.addEventListener("keydown", handleEscape);
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "unset";
    }

    return () => {
      document.removeEventListener("keydown", handleEscape);
      document.body.style.overflow = "unset";
    };
  }, [mobileOpen, onCloseMobile]);
  const handleLogout = async () => {
    try {
      await logout();
      router.push("/login");
    } catch (error) {
      console.error("Failed to logout:", error);
    }
  };

  const displayName = user?.email || user?.displayName || "User";
  const ThemeIcon = theme === "light" ? Moon : Sun;

  // Debug: Log userId to help troubleshoot document visibility issues
  useEffect(() => {
    if (userId) {
      console.log("🔑 Current User ID:", userId);
      console.log("📧 User Email:", user?.email);
      console.log("👤 User UID:", user?.uid);
    }
  }, [userId, user]);

  // Desktop collapsed view
  if (collapsed && !mobileOpen) {
    return (
      <div className="hidden lg:flex lg:w-16 p-2 h-full lg:sticky lg:top-6 self-start transition-all duration-300 flex-col items-center space-y-3">
        <button
          onClick={() => setCollapsed(false)}
          title="Expand profile"
          className="p-2.5 rounded-lg bg-white dark:bg-gray-800 shadow hover:shadow-md transition text-gray-700 dark:text-gray-300"
        >
          <ChevronLeft size={20} />
        </button>
        {user ? (
          user.photoURL ? (
            <Image
              src={user.photoURL}
              alt="Profile"
              width={40}
              height={40}
              className="rounded-full"
            />
          ) : (
            <div className="w-10 h-10 rounded-full bg-blue-600 flex items-center justify-center text-white font-medium text-sm">
              {user.email?.[0].toUpperCase() || "?"}
            </div>
          )
        ) : (
          <div className="w-10 h-10 rounded-full bg-gray-400 flex items-center justify-center text-white">
            <User size={20} />
          </div>
        )}
      </div>
    );
  }

  return (
    <>
      {/* Mobile Overlay */}
      {mobileOpen && (
        <div
          className="lg:hidden fixed inset-0 bg-black/50 z-40 transition-opacity duration-300"
          onClick={onCloseMobile}
        />
      )}

      {/* Right Sidebar Content */}
      <div
        className={`
          fixed lg:static inset-y-0 right-0 z-50
          w-[85vw] sm:w-[320px] lg:w-80
          bg-white dark:bg-gray-800 
          lg:rounded-2xl shadow-xl
          h-full lg:sticky lg:top-6 self-start
          flex flex-col
          transition-all duration-300 ease-in-out
          ${mobileOpen ? "translate-x-0" : "translate-x-full lg:translate-x-0"}
        `}
      >
        {/* Header with tabs */}
        <div className="flex-shrink-0 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between p-4">
            <h2 className="text-lg font-bold text-gray-900 dark:text-white">
              Settings
            </h2>
            <button
              onClick={() => (mobileOpen ? onCloseMobile() : setCollapsed(true))}
              className="p-2 rounded-md bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 transition"
              aria-label={mobileOpen ? "Close" : "Collapse"}
            >
              <ChevronRight size={18} />
            </button>
          </div>

          {/* Tabs */}
          <div className="flex border-b border-gray-200 dark:border-gray-700">
            <button
              onClick={() => setActiveTab("account")}
              className={`flex-1 px-4 py-3 text-sm font-medium transition-colors relative ${
                activeTab === "account"
                  ? "text-blue-600 dark:text-blue-400"
                  : "text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200"
              }`}
            >
              <User size={16} className="inline mr-2" />
              Account
              {activeTab === "account" && (
                <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-600 dark:bg-blue-400" />
              )}
            </button>
            <button
              onClick={() => setActiveTab("documents")}
              className={`flex-1 px-4 py-3 text-sm font-medium transition-colors relative ${
                activeTab === "documents"
                  ? "text-blue-600 dark:text-blue-400"
                  : "text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200"
              }`}
            >
              <FileText size={16} className="inline mr-2" />
              Documents
              {activeTab === "documents" && (
                <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-600 dark:bg-blue-400" />
              )}
            </button>
          </div>
        </div>

        {/* Scrollable Content */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6">
          {activeTab === "account" ? (
            <>
              {/* Account Tab Content */}
              {user ? (
                <div className="space-y-4">
                  <div className="flex items-center gap-3">
                    {user.photoURL ? (
                      <Image
                        src={user.photoURL}
                        alt="Profile"
                        width={48}
                        height={48}
                        className="rounded-full"
                      />
                    ) : (
                      <div className="w-12 h-12 rounded-full bg-blue-600 flex items-center justify-center text-white font-medium text-lg">
                        {user.email?.[0].toUpperCase() || "?"}
                      </div>
                    )}
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-semibold text-gray-900 dark:text-white truncate">
                        {displayName}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
                        {user.email}
                      </p>
                    </div>
                  </div>

                  {/* Tenant ID */}
                  <div className="bg-gray-50 dark:bg-gray-900/50 rounded-lg p-3 space-y-2">
                    <div>
                      <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">
                        User ID (Tenant)
                      </p>
                      <p className="text-xs font-mono text-gray-700 dark:text-gray-300 break-all">
                        {userId || "Not available"}
                      </p>
                    </div>
                  </div>

                  {/* Logout Button */}
                  <button
                    onClick={handleLogout}
                    className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors font-medium text-sm"
                  >
                    <LogOut size={16} />
                    Logout
                  </button>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="text-center p-6 bg-gray-50 dark:bg-gray-900/50 rounded-lg">
                    <div className="w-16 h-16 mx-auto mb-3 rounded-full bg-gray-300 dark:bg-gray-600 flex items-center justify-center">
                      <User size={32} className="text-gray-600 dark:text-gray-400" />
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                      Not logged in
                    </p>
                    <button
                      onClick={() => router.push("/login")}
                      className="w-full px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium text-sm"
                    >
                      Login
                    </button>
                  </div>
                </div>
              )}

              {/* Theme Toggle */}
              <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                <button
                  onClick={onToggleTheme}
                  className="w-full flex items-center justify-between px-4 py-3 rounded-lg bg-gray-50 dark:bg-gray-900/50 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                >
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Theme
                  </span>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-gray-500 dark:text-gray-400 capitalize">
                      {theme}
                    </span>
                    <ThemeIcon
                      size={18}
                      className="text-gray-600 dark:text-gray-400"
                    />
                  </div>
                </button>
              </div>
            </>
          ) : (
            <>
              {/* Documents Tab Content */}
              <div className="space-y-4">
                {/* Refresh Button */}
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300">
                    Gestione Documenti
                  </h3>
                  <button
                    onClick={onRefreshDocuments}
                    disabled={isLoadingDocuments}
                    className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors disabled:opacity-50"
                    title="Refresh documents"
                  >
                    <RefreshCw
                      size={16}
                      className={`text-gray-600 dark:text-gray-400 ${
                        isLoadingDocuments ? "animate-spin" : ""
                      }`}
                    />
                  </button>
                </div>

                {/* Status Alert */}
                {statusAlert && (
                  <AlertMessage alert={statusAlert} />
                )}

                {/* Document List */}
                <DocumentList
                  documents={documents}
                  isLoading={isLoadingDocuments}
                  onDeleteDocument={onDeleteDocument}
                  onRefresh={onRefreshDocuments}
                />
              </div>
            </>
          )}
        </div>
      </div>
    </>
  );
};
