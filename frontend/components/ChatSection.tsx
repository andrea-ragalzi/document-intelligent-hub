import { FormEvent, useState, useRef, useEffect } from "react";
import {
  MessageSquare,
  CornerDownLeft,
  Loader,
  Paperclip,
  Target,
} from "lucide-react";
import type { ChatMessage } from "@/lib/types";
import { ChatMessageDisplay } from "./ChatMessageDisplay";
import { UseCaseSelector } from "./UseCaseSelector";

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
  selectedUseCaseId: string;
  onSelectUseCase: (id: string) => void;
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
  selectedUseCaseId,
  onSelectUseCase,
}) => {
  const [isUseCaseSelectorOpen, setIsUseCaseSelectorOpen] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const isChatDisabled = !hasDocuments && !isCheckingDocuments;

  // Reset textarea height when query is cleared
  useEffect(() => {
    if (query === "" && textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  }, [query]);
  return (
    <div className="w-full h-full flex flex-col bg-white dark:bg-gray-900 transition-colors duration-200 ease-in-out font-[Inter] relative">
      <div className="flex-1 p-4 sm:p-6 pb-40 overflow-y-auto">
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

      {/* Gemini-Style Input Bar - Two-Row Layout */}
      <form
        onSubmit={onQuerySubmit}
        className="fixed bottom-0 left-0 right-0 lg:left-72 xl:right-96 bg-gray-900 py-4 px-4 transition-all duration-200 ease-in-out"
      >
        <div className="max-w-4xl mx-auto">
          {/* Single Pill Container with Two Sections */}
          <div className="bg-gray-800 rounded-3xl shadow-lg px-4 py-3">
            {/* Top Section - Input Field */}
            <div className="mb-4">
              <textarea
                ref={textareaRef}
                value={query}
                onChange={(e) => onQueryChange(e.target.value)}
                disabled={isQuerying || !userId || isChatDisabled}
                placeholder={
                  isChatDisabled ? "Upload document first..." : "Message..."
                }
                rows={1}
                className="w-full px-2 py-2 text-base bg-transparent focus:outline-none disabled:cursor-not-allowed transition-all duration-200 text-white placeholder-gray-500 resize-none overflow-hidden"
                style={{
                  minHeight: "2.5rem",
                  maxHeight: "12rem",
                }}
                onInput={(e) => {
                  const target = e.target as HTMLTextAreaElement;
                  target.style.height = "auto";
                  target.style.height = `${Math.min(
                    target.scrollHeight,
                    192
                  )}px`;
                }}
              />
            </div>

            {/* Bottom Section - Action Buttons */}
            <div className="flex items-center justify-between">
              {/* Left Actions */}
              <div className="flex items-center gap-1">
                {/* Upload/Attach Button */}
                <button
                  type="button"
                  onClick={onOpenUploadModal}
                  disabled={!userId}
                  className="flex items-center justify-center h-9 w-9 rounded-full text-gray-400 hover:text-gray-200 hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed flex-shrink-0 transition-all duration-200"
                  title="Upload document"
                >
                  <Paperclip size={18} />
                </button>

                {/* Use Case Selector Button */}
                <button
                  type="button"
                  onClick={() => setIsUseCaseSelectorOpen(true)}
                  disabled={!userId}
                  className={`flex items-center justify-center h-9 w-9 rounded-full disabled:opacity-50 disabled:cursor-not-allowed flex-shrink-0 transition-all duration-200 ${
                    selectedUseCaseId === "AUTO"
                      ? "text-gray-400 hover:text-gray-200 hover:bg-gray-700"
                      : "text-emerald-400 hover:text-emerald-300 hover:bg-gray-700"
                  }`}
                  title={
                    selectedUseCaseId === "AUTO"
                      ? "Select Use Case"
                      : `Use Case: ${selectedUseCaseId}`
                  }
                >
                  <Target size={18} />
                </button>
              </div>

              {/* Right Action - Send Button */}
              <button
                type="submit"
                disabled={
                  isQuerying || !query.trim() || !userId || isChatDisabled
                }
                className={`flex items-center justify-center h-9 w-9 rounded-full transition-all duration-200 flex-shrink-0 ${
                  isQuerying || !query.trim() || !userId || isChatDisabled
                    ? "bg-gray-700 text-gray-500 cursor-not-allowed"
                    : "bg-indigo-600 text-white hover:bg-indigo-500"
                }`}
              >
                {isQuerying ? (
                  <Loader size={18} className="animate-spin" />
                ) : (
                  <CornerDownLeft size={18} />
                )}
              </button>
            </div>
          </div>
        </div>
      </form>

      {/* Use Case Selector Modal */}
      <UseCaseSelector
        isOpen={isUseCaseSelectorOpen}
        selectedUseCaseId={selectedUseCaseId}
        onSelectUseCase={onSelectUseCase}
        onClose={() => setIsUseCaseSelectorOpen(false)}
      />
    </div>
  );
};
