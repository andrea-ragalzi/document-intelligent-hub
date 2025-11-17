import { FormEvent } from "react";
import { MessageSquare, CornerDownLeft, Loader, Plus } from "lucide-react";
import type { ChatMessage } from "@/lib/types";
import { ChatMessageDisplay } from "./ChatMessageDisplay";

interface ChatSectionProps {
  chatHistory: ChatMessage[];
  query: string;
  isQuerying: boolean;
  userId: string | null;
  chatEndRef: React.RefObject<HTMLDivElement | null>;
  onQueryChange: (value: string) => void;
  onQuerySubmit: (e: FormEvent) => void;
  hasDocuments: boolean;
  isCheckingDocuments: boolean;
  onOpenUploadModal: () => void;
}
export const ChatSection: React.FC<ChatSectionProps> = ({
  chatHistory,
  query,
  isQuerying,
  userId,
  chatEndRef,
  onQueryChange,
  onQuerySubmit,
  hasDocuments,
  isCheckingDocuments,
  onOpenUploadModal,
}) => {
  const isChatDisabled = !hasDocuments && !isCheckingDocuments;
  return (
    <div className="w-full h-full flex flex-col bg-white dark:bg-gray-900 transition-colors duration-200 ease-in-out font-[Inter] relative">
      <div className="flex-1 p-4 sm:p-6 pb-32 overflow-y-auto">
        <div className="max-w-4xl mx-auto">
          {chatHistory.length === 0 ? (
            <div className="text-center p-8 sm:p-16 text-gray-400">
              <MessageSquare
                size={48}
                className="sm:size-16 mx-auto mb-4 text-indigo-200 dark:text-indigo-800"
              />
              {isChatDisabled ? (
                <>
                  <p className="font-bold text-lg text-yellow-600 dark:text-yellow-400">
                    ⚠️ No Documents Uploaded
                  </p>
                  <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">
                    Please upload at least one PDF document before starting a
                    conversation.
                  </p>
                </>
              ) : isCheckingDocuments ? (
                <>
                  <p className="font-bold text-lg text-gray-500 dark:text-gray-300">
                    Checking documents...
                  </p>
                </>
              ) : (
                <>
                  <p className="font-bold text-lg text-gray-900 dark:text-gray-100 font-medium">
                    Ready to search.
                  </p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    Ask your first question about the uploaded documents.
                  </p>
                </>
              )}
            </div>
          ) : isQuerying ? (
            <>
              {chatHistory.map((msg, index) => (
                <ChatMessageDisplay key={index} msg={msg} />
              ))}
              {/* Skeleton Loader - Animate Pulse with Gradient */}
              <div className="mt-4 space-y-3 animate-pulse">
                <div className="h-4 bg-gradient-to-r from-gray-200 via-gray-300 to-gray-200 dark:from-gray-700 dark:via-gray-600 dark:to-gray-700 rounded-lg w-3/4"></div>
                <div className="h-4 bg-gradient-to-r from-gray-200 via-gray-300 to-gray-200 dark:from-gray-700 dark:via-gray-600 dark:to-gray-700 rounded-lg w-full"></div>
                <div className="h-4 bg-gradient-to-r from-gray-200 via-gray-300 to-gray-200 dark:from-gray-700 dark:via-gray-600 dark:to-gray-700 rounded-lg w-5/6"></div>
              </div>
            </>
          ) : (
            chatHistory.map((msg, index) => (
              <ChatMessageDisplay key={index} msg={msg} />
            ))
          )}
          <div ref={chatEndRef} />
        </div>
      </div>

      {/* Input Fluttuante con Ombra Indaco Premium */}
      <form
        onSubmit={onQuerySubmit}
        className="fixed bottom-0 left-0 right-0 lg:left-72 xl:right-96 bg-white/95 dark:bg-gray-900/95 backdrop-blur-sm border-t-2 border-gray-200 dark:border-gray-700 shadow-2xl shadow-indigo-500/30 py-4 sm:py-6 px-4 transition-all duration-200 ease-in-out"
      >
        <div className="max-w-3xl mx-auto flex items-center gap-2 sm:gap-3">
          {/* Upload Button - Premium Shadow */}
          <button
            type="button"
            onClick={onOpenUploadModal}
            disabled={!userId}
            className="flex items-center justify-center h-10 w-10 sm:h-12 sm:w-12 rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 shadow-md hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed flex-shrink-0 transition-all duration-200 ease-in-out"
            title="Upload document"
          >
            <Plus size={18} className="sm:size-5" />
          </button>

          {/* Query Input - Enterprise Focus Ring */}
          <input
            type="text"
            value={query}
            onChange={(e) => onQueryChange(e.target.value)}
            disabled={isQuerying || !userId || isChatDisabled}
            placeholder={
              isChatDisabled ? "Upload document first..." : "Ask a question..."
            }
            className="flex-grow px-3 py-2.5 sm:px-4 sm:py-3 text-sm sm:text-base border-2 border-gray-300 dark:border-gray-600 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 disabled:bg-gray-100 dark:disabled:bg-gray-800 transition-all duration-200 ease-in-out bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 placeholder-gray-500 dark:placeholder-gray-400 font-medium"
          />

          {/* Submit Button - Premium Shadow */}
          <button
            type="submit"
            disabled={isQuerying || !query.trim() || !userId || isChatDisabled}
            className={`flex items-center justify-center h-10 w-10 sm:h-12 sm:w-12 rounded-lg shadow-md hover:shadow-lg transition-all duration-200 ease-in-out flex-shrink-0 ${
              isQuerying || !query.trim() || !userId || isChatDisabled
                ? "bg-gray-300 text-gray-600 cursor-not-allowed dark:bg-gray-700 dark:text-gray-400"
                : "bg-indigo-600 text-white hover:bg-indigo-700"
            }`}
          >
            {isQuerying ? (
              <Loader size={18} className="animate-spin sm:size-5" />
            ) : (
              <CornerDownLeft size={18} className="sm:size-5" />
            )}
          </button>
        </div>
      </form>
    </div>
  );
};
