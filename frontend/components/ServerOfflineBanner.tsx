"use client";

import { WifiOff, X, RefreshCw } from "lucide-react";
import { useUIStore } from "@/stores/uiStore";

interface ServerOfflineBannerProps {
  onRetry: () => void;
  isRetrying?: boolean;
}

/**
 * Banner shown when backend server is unreachable
 * Allows users to continue using offline features (reading conversations)
 */
export const ServerOfflineBanner: React.FC<ServerOfflineBannerProps> = ({
  onRetry,
  isRetrying = false,
}) => {
  const { dismissServerOfflineBanner } = useUIStore();

  return (
    <div className="bg-yellow-50 dark:bg-yellow-900/20 border-b border-yellow-200 dark:border-yellow-800">
      <div className="max-w-7xl mx-auto px-4 py-3">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-3 flex-1">
            <div className="flex-shrink-0">
              <WifiOff
                size={20}
                className="text-yellow-600 dark:text-yellow-400"
              />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-yellow-800 dark:text-yellow-200">
                Server Unreachable
              </p>
              <p className="text-xs text-yellow-700 dark:text-yellow-300 mt-0.5">
                You can still read saved conversations. Upload and new queries
                unavailable.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 flex-shrink-0">
            <button
              onClick={onRetry}
              disabled={isRetrying}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-yellow-800 dark:text-yellow-200 bg-yellow-100 dark:bg-yellow-900/40 hover:bg-yellow-200 dark:hover:bg-yellow-900/60 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              aria-label="Retry connection"
            >
              <RefreshCw
                size={14}
                className={isRetrying ? "animate-spin" : ""}
              />
              Retry
            </button>

            <button
              onClick={dismissServerOfflineBanner}
              className="p-1.5 text-yellow-600 dark:text-yellow-400 hover:bg-yellow-100 dark:hover:bg-yellow-900/40 rounded-md transition-colors"
              aria-label="Close banner"
            >
              <X size={16} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
