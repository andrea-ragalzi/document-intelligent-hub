import { X } from "lucide-react";
import Image from "next/image";
import TierLimitsDisplay from "../TierLimitsDisplay";
import { User } from "firebase/auth";

interface Document {
  filename: string;
  chunks_count: number;
  language?: string;
}

interface MenuProfileSectionProps {
  user: User | null;
  userId: string | null;
  displayName: string;
  documents: Document[] | undefined;
  currentQueries: number;
  onClose: () => void;
  onLogout: () => void;
}

export const MenuProfileSection: React.FC<MenuProfileSectionProps> = ({
  user,
  userId,
  displayName,
  documents,
  currentQueries,
  onClose,
  onLogout,
}) => {
  return (
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
          <p className="text-xs text-indigo-700 dark:text-indigo-200 truncate">{user?.email}</p>
        </div>
        <button
          onClick={onClose}
          className="h-11 w-11 flex items-center justify-center rounded-lg hover:bg-indigo-100 dark:hover:bg-indigo-800 transition-all duration-200 ease-in-out xl:hidden focus:outline-none focus:ring-3 focus:ring-focus"
        >
          <X size={20} className="text-indigo-700 dark:text-indigo-200" />
        </button>
      </div>
      <div className="bg-indigo-100 dark:bg-indigo-900 rounded-lg p-3 mb-3">
        <p className="text-xs text-indigo-700 dark:text-indigo-200 mb-1">User ID</p>
        <p className="text-xs font-mono text-indigo-900 dark:text-indigo-50 break-all">
          {userId || "Non disponibile"}
        </p>
      </div>

      <div className="mb-3">
        <TierLimitsDisplay
          currentDocuments={documents?.length || 0}
          currentQueries={currentQueries}
        />
      </div>

      <button
        onClick={onLogout}
        className="min-h-[44px] w-full flex items-center justify-center gap-2 px-4 py-2 text-sm font-medium text-indigo-900 dark:text-indigo-50 border-2 border-indigo-300 dark:border-indigo-700 hover:bg-indigo-100 dark:hover:bg-indigo-800 rounded-lg transition-all duration-200 focus:outline-none focus:ring-3 focus:ring-focus"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
          <polyline points="16 17 21 12 16 7" />
          <line x1="21" y1="12" x2="9" y2="12" />
        </svg>
        Logout
      </button>
    </div>
  );
};
