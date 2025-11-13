import { FileText, ChevronLeft, ChevronRight, X } from "lucide-react";
import { useState, useEffect } from "react";
import { UploadSection } from "./UploadSection";
import { ConversationList } from "./ConversationList";
import type { SavedConversation, AlertState } from "@/lib/types";
import { FormEvent, ChangeEvent } from "react";

interface SidebarProps {
  userId: string | null;
  file: File | null;
  isUploading: boolean;
  uploadAlert: AlertState;
  statusAlert: AlertState | null;
  savedConversations: SavedConversation[];
  mobileOpen: boolean;
  onCloseMobile: () => void;
  onFileChange: (e: ChangeEvent<HTMLInputElement>) => void;
  onUpload: (e: FormEvent) => void;
  onLoadConversation: (conv: SavedConversation) => void;
  onDeleteConversation: (id: string, name: string) => void;
  onRenameConversation: (id: string, currentName: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  userId,
  file,
  isUploading,
  uploadAlert,
  statusAlert,
  savedConversations,
  mobileOpen,
  onCloseMobile,
  onFileChange,
  onUpload,
  onLoadConversation,
  onDeleteConversation,
  onRenameConversation,
}) => {
  const [collapsed, setCollapsed] = useState(false);

  // Close mobile menu when clicking outside or on escape
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") onCloseMobile();
    };

    if (mobileOpen) {
      document.addEventListener("keydown", handleEscape);
      // Prevent body scroll when menu is open
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "unset";
    }

    return () => {
      document.removeEventListener("keydown", handleEscape);
      document.body.style.overflow = "unset";
    };
  }, [mobileOpen, onCloseMobile]);

  // Desktop collapsed view
  if (collapsed && !mobileOpen) {
    return (
      <div className="hidden lg:flex lg:w-16 p-2 h-full lg:sticky lg:top-6 self-start transition-all duration-300 flex-col items-center space-y-3">
        <button
          onClick={() => setCollapsed(false)}
          title="Expand sidebar"
          className="p-2.5 rounded-lg bg-white dark:bg-gray-800 shadow hover:shadow-md transition text-gray-700 dark:text-gray-300"
        >
          <ChevronRight size={20} />
        </button>
        <div className="w-10 h-10 rounded-lg bg-blue-600 flex items-center justify-center text-white">
          <FileText size={20} />
        </div>
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

      {/* Sidebar Content */}
      <div
        className={`
          fixed lg:static inset-y-0 left-0 z-50
          w-[85vw] sm:w-[320px] lg:w-1/3
          bg-white dark:bg-gray-800 
          lg:rounded-2xl shadow-xl
          h-full lg:sticky lg:top-6 self-start
          p-4 sm:p-6 space-y-4 sm:space-y-6
          transition-all duration-300 ease-in-out
          ${mobileOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"}
        `}
      >
        {/* Header */}
        <div className="flex items-start justify-between">
          <div className="min-w-0 flex-1">
            <h1 className="text-2xl sm:text-3xl font-extrabold text-gray-900 dark:text-white mb-2 flex items-center">
              <FileText
                className="mr-2 sm:mr-3 text-blue-600 flex-shrink-0"
                size={24}
              />
              <span className="truncate">Document RAG</span>
            </h1>
            <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400 mb-4 flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-0">
              <span className="whitespace-nowrap">User ID:</span>
              <span
                className={`font-mono font-medium sm:ml-2 px-2 py-0.5 rounded-md text-xs inline-block truncate max-w-[200px] ${
                  userId
                    ? "bg-blue-100 text-blue-700 dark:bg-blue-900/50 dark:text-blue-300"
                    : "bg-yellow-100 text-yellow-700"
                }`}
                title={userId || "Not available"}
              >
                {userId ? userId : "Not available"}
              </span>
            </p>
          </div>

          {/* Close button (mobile) and collapse button (desktop) */}
          <div className="flex items-center ml-3 flex-shrink-0 gap-2">
            <button
              onClick={onCloseMobile}
              className="lg:hidden p-2 rounded-md bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 transition"
              aria-label="Close menu"
            >
              <X size={18} />
            </button>
            <button
              onClick={() => setCollapsed(true)}
              title="Collapse sidebar"
              className="hidden lg:block p-2 rounded-md bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 transition"
            >
              <ChevronLeft size={18} />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="overflow-y-auto h-[calc(100vh-180px)] lg:h-auto space-y-4 sm:space-y-6">
          <UploadSection
            file={file}
            isUploading={isUploading}
            userId={userId}
            uploadAlert={uploadAlert}
            statusAlert={statusAlert}
            onFileChange={onFileChange}
            onUpload={onUpload}
          />

          <ConversationList
            conversations={savedConversations}
            onLoad={(conv) => {
              onLoadConversation(conv);
              onCloseMobile(); // Close mobile menu after loading
            }}
            onDelete={onDeleteConversation}
            onRename={onRenameConversation}
          />
        </div>
      </div>
    </>
  );
};
