/**
 * Empty state component for ChatSection
 */

import { Loader, AlertTriangle, MessageSquare, Paperclip } from "lucide-react";

interface EmptyStateProps {
  isCheckingDocuments: boolean;
  isServerOnline: boolean;
  isLimitReached: boolean;
  noDocuments: boolean;
}

export function ChatEmptyState({
  isCheckingDocuments,
  isServerOnline,
  isLimitReached,
  noDocuments,
}: EmptyStateProps) {
  if (isCheckingDocuments) {
    return (
      <>
        <p className="font-bold text-lg text-gray-500 dark:text-gray-300">Checking documents...</p>
        <Loader size={24} className="animate-spin mx-auto mt-4 text-indigo-500" />
      </>
    );
  }

  if (isServerOnline === false) {
    return (
      <div className="bg-red-100 dark:bg-red-900/30 p-4 rounded-xl border border-red-200 dark:border-red-700">
        <p className="font-bold text-lg text-red-700 dark:text-red-400 flex items-center justify-center">
          <AlertTriangle size={20} className="mr-2" />
          Server Offline
        </p>
        <p className="text-sm text-red-600 dark:text-red-300 mt-2 text-center">
          The backend is currently unavailable. Please check your connection or try again later.
        </p>
      </div>
    );
  }

  if (isLimitReached) {
    return (
      <div className="bg-orange-100 dark:bg-orange-900/30 p-4 rounded-xl border border-orange-200 dark:border-orange-700">
        <p className="font-bold text-lg text-orange-700 dark:text-orange-400 flex items-center justify-center">
          <AlertTriangle size={20} className="mr-2" />
          Query Limit Reached
        </p>
        <p className="text-sm text-orange-600 dark:text-orange-300 mt-2 text-center">
          You&apos;ve reached your daily query limit. Upgrade your plan or try again tomorrow.
        </p>
      </div>
    );
  }

  if (noDocuments) {
    return (
      <>
        <MessageSquare size={48} className="mx-auto text-indigo-400 dark:text-indigo-500" />
        <p className="font-bold text-lg text-gray-500 dark:text-gray-300">
          No documents uploaded yet
        </p>
        <p className="text-sm text-gray-400 dark:text-gray-500 max-w-md mx-auto">
          <Paperclip size={14} className="inline mr-1" />
          Upload a PDF document to start asking questions
        </p>
      </>
    );
  }

  return (
    <>
      <MessageSquare size={48} className="mx-auto text-indigo-400 dark:text-indigo-500" />
      <p className="font-bold text-lg text-gray-500 dark:text-gray-300">Start a conversation</p>
      <p className="text-sm text-gray-400 dark:text-gray-500">
        Ask me anything about your documents!
      </p>
    </>
  );
}
