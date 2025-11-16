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
    <div className="w-full h-full flex flex-col bg-white dark:bg-gray-800 rounded-2xl shadow-xl transition-colors duration-500">
      <div className="flex-1 p-3 sm:p-6 pt-6 sm:pt-8 overflow-y-auto bg-gray-50 dark:bg-gray-900/50">
        {chatHistory.length === 0 ? (
          <div className="text-center p-6 sm:p-12 text-gray-400">
            <MessageSquare
              size={48}
              className="sm:size-16 mx-auto mb-4 text-blue-200"
            />
            {isChatDisabled ? (
              <>
                <p className="font-bold text-lg text-yellow-600 dark:text-yellow-400">
                  ⚠️ No Documents Uploaded
                </p>
                <p className="text-sm dark:text-gray-400 mt-2">
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
                <p className="font-bold text-lg text-gray-500 dark:text-gray-300">
                  Ready to search.
                </p>
                <p className="text-sm dark:text-gray-400">
                  Ask your first question about the uploaded documents.
                </p>
              </>
            )}
          </div>
        ) : (
          chatHistory.map((msg, index) => (
            <ChatMessageDisplay key={index} msg={msg} />
          ))
        )}
        <div ref={chatEndRef} />
      </div>
      <form
        onSubmit={onQuerySubmit}
        className="sticky bottom-0 p-3 sm:p-4 border-t border-gray-200 dark:border-gray-700 bg-white/90 dark:bg-gray-800/90 backdrop-blur-sm rounded-b-2xl"
      >
        <div className="flex items-center space-x-2 sm:space-x-3">
          {/* Upload Button */}
          <button
            type="button"
            onClick={onOpenUploadModal}
            disabled={!userId}
            className="flex items-center justify-center p-2.5 sm:p-3 rounded-lg bg-blue-600 text-white hover:bg-blue-700 shadow-md transition duration-200 flex-shrink-0 disabled:opacity-50 disabled:cursor-not-allowed"
            title="Upload document"
          >
            <Plus size={18} className="sm:size-5" />
          </button>

          {/* Query Input */}
          <input
            type="text"
            value={query}
            onChange={(e) => onQueryChange(e.target.value)}
            disabled={isQuerying || !userId || isChatDisabled}
            placeholder={
              isChatDisabled ? "Upload document first..." : "Ask a question..."
            }
            className="flex-grow p-2.5 sm:p-3 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500 shadow-inner disabled:bg-gray-100 transition text-sm bg-white dark:bg-gray-900 dark:border-gray-600 dark:text-white disabled:dark:bg-gray-700"
          />

          {/* Submit Button */}
          <button
            type="submit"
            disabled={isQuerying || !query.trim() || !userId || isChatDisabled}
            className={`flex items-center justify-center p-2.5 sm:p-3 rounded-lg shadow-md transition duration-200 flex-shrink-0 ${
              isQuerying || !query.trim() || !userId || isChatDisabled
                ? "bg-gray-300 text-gray-600 cursor-not-allowed dark:bg-gray-600 dark:text-gray-300"
                : "bg-blue-600 text-white hover:bg-blue-700 hover:shadow-lg"
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
