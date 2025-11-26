import { FormEvent, useState, useRef, useEffect } from "react";
import {
  MessageSquare,
  CornerDownLeft,
  Loader,
  Paperclip,
  AlertTriangle,
} from "lucide-react";
import type { ChatMessage } from "@/lib/types";
import { ChatMessageDisplay } from "./ChatMessageDisplay";
import { OutputLanguageSelector } from "./OutputLanguageSelector";
import { getLanguageFlag } from "@/lib/languages";

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
  selectedOutputLanguage: string;
  onSelectOutputLanguage: (code: string) => void;
  isServerOnline?: boolean;
  isLimitReached?: boolean;
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
  selectedOutputLanguage,
  onSelectOutputLanguage,
  isServerOnline = true,
  isLimitReached = false,
}) => {
  const [isLanguageSelectorOpen, setIsLanguageSelectorOpen] = useState(false);
  const [languageFlag, setLanguageFlag] = useState<string>("🌍");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Calculate specific disable reasons
  const noDocuments = !hasDocuments && !isCheckingDocuments;
  const isChatDisabled = noDocuments || !isServerOnline || isLimitReached;

  // Fetch language flag when selectedOutputLanguage changes
  useEffect(() => {
    getLanguageFlag(selectedOutputLanguage).then(setLanguageFlag);
  }, [selectedOutputLanguage]);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    const scrollToBottom = () => {
      if (chatEndRef.current) {
        chatEndRef.current.scrollIntoView({ behavior: "smooth", block: "end" });
      }
    };

    // Small delay to ensure DOM is updated
    const timeoutId = setTimeout(scrollToBottom, 100);
    return () => clearTimeout(timeoutId);
  }, [chatHistory, isQuerying]);

  // Handle form submission with textarea reset
  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!query.trim() || isQuerying || !userId || isChatDisabled) return;

    onQuerySubmit(e);
    // Reset textarea height immediately after submission
    if (textareaRef.current) {
      textareaRef.current.style.height = "44px"; // Reset to initial height
    }
  };

  // Auto-resize textarea with dynamic height calculation (Gemini-style)
  const handleTextareaInput = (e: React.FormEvent<HTMLTextAreaElement>) => {
    const target = e.target as HTMLTextAreaElement;

    // Reset height to auto to get proper scrollHeight
    target.style.height = "44px";

    // Calculate new height (max ~6 lines = 144px)
    const newHeight = Math.min(target.scrollHeight, 144);
    target.style.height = `${newHeight}px`;
  };

  // Handler for onChange event that extracts the value
  const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    onQueryChange(e.target.value);
    handleTextareaInput(e);
  };

  return (
    <div className="w-full h-full flex flex-col bg-indigo-50 dark:bg-indigo-950 transition-colors duration-200 ease-in-out font-[Inter] relative pb-0">
      {/* Scrollable Chat Area: Altezza calcolata per lasciare spazio all'input bar */}
      <div
        className="p-4 sm:p-6 overflow-y-auto w-full flex-grow pb-0"
        // Adjust height to allow for the sticky input bar (approx 100px height for the bar)
        style={{ height: "calc(100vh - 100px)" }}
      >
        <div className="max-w-4xl mx-auto">
          {chatHistory.length === 0 ? (
            <div className="text-center p-8 sm:p-16 text-indigo-700 dark:text-indigo-200">
              <MessageSquare
                size={48}
                className="sm:size-16 mx-auto mb-4 text-indigo-300"
              />
              {isCheckingDocuments ? (
                <>
                  <p className="font-bold text-lg text-gray-500 dark:text-gray-300">
                    Checking documents...
                  </p>
                  <Loader
                    size={24}
                    className="animate-spin mx-auto mt-4 text-indigo-500"
                  />
                </>
              ) : !isServerOnline ? (
                <div className="bg-red-100 dark:bg-red-900/30 p-4 rounded-xl border border-red-200 dark:border-red-700">
                  <p className="font-bold text-lg text-red-700 dark:text-red-400 flex items-center justify-center">
                    <AlertTriangle size={20} className="mr-2" />
                    Server Offline
                  </p>
                  <p className="text-sm text-indigo-900 dark:text-indigo-50 mt-2">
                    The server is currently offline. Please try again later.
                  </p>
                </div>
              ) : isLimitReached ? (
                <div className="bg-orange-100 dark:bg-orange-900/30 p-4 rounded-xl border border-orange-200 dark:border-orange-700">
                  <p className="font-bold text-lg text-orange-700 dark:text-orange-400 flex items-center justify-center">
                    <AlertTriangle size={20} className="mr-2" />
                    Query Limit Reached
                  </p>
                  <p className="text-sm text-indigo-900 dark:text-indigo-50 mt-2">
                    You&apos;ve reached your daily query limit. Upgrade your
                    plan or try again tomorrow.
                  </p>
                </div>
              ) : noDocuments ? (
                <div className="bg-yellow-100 dark:bg-yellow-900/30 p-4 rounded-xl border border-yellow-200 dark:border-yellow-700">
                  <p className="font-bold text-lg text-yellow-700 dark:text-yellow-400 flex items-center justify-center">
                    <AlertTriangle size={20} className="mr-2" />
                    No Documents Uploaded
                  </p>
                  <p className="text-sm text-indigo-900 dark:text-indigo-50 mt-2">
                    Please upload at least one PDF document before starting a
                    conversation.
                  </p>
                </div>
              ) : (
                <>
                  <p className="font-bold text-xl text-gray-900 dark:text-gray-100">
                    Ready to chat.
                  </p>
                  <p className="text-md text-gray-500 dark:text-gray-400 mt-2">
                    Send your first question about your uploaded documents.
                  </p>
                </>
              )}
            </div>
          ) : (
            // Display history and optional skeleton loader
            <>
              {chatHistory.map((msg, index) => (
                <ChatMessageDisplay key={index} msg={msg} />
              ))}
              {isQuerying && (
                <div className="flex justify-start mb-6 px-1 sm:px-2">
                  <div className="flex-shrink-0 mr-2 w-8 h-8"></div>
                  <div className="max-w-[85%] sm:max-w-[80%] flex flex-col">
                    <div className="text-xs font-medium mb-1 text-indigo-600 dark:text-indigo-400 pl-2">
                      Assistente
                    </div>
                    <div className="p-3 sm:p-4 rounded-xl shadow-md bg-white dark:bg-gray-800 rounded-tl-sm border border-gray-100 dark:border-gray-700">
                      {/* Skeleton Loader - Animate Pulse with Gradient */}
                      <div className="mt-1 space-y-2 animate-pulse">
                        <div className="h-3 bg-indigo-200 dark:bg-indigo-700/50 rounded-lg w-3/4"></div>
                        <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded-lg w-full"></div>
                        <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded-lg w-5/6"></div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
          <div ref={chatEndRef} />
        </div>
      </div>

      {/* Gemini-style Input Bar - Sticky bottom with elegant spacing */}
      <form
        onSubmit={handleSubmit}
        className="sticky bottom-0 left-0 right-0 bg-transparent sm:bg-gradient-to-t sm:from-indigo-50 sm:via-indigo-50 sm:to-transparent sm:dark:from-indigo-950 sm:dark:via-indigo-950 sm:dark:to-transparent pt-0 pb-0 -mx-4 md:mx-0 md:pt-4 md:pb-3 md:px-4 transition-all duration-200 ease-in-out z-10"
      >
        <div className="max-w-4xl md:mx-auto">
          {/* Gemini-inspired Input Container */}
          <div
            className="relative bg-indigo-50 dark:bg-indigo-950 
            rounded-3xl md:rounded-[32px] 
            shadow-md md:shadow-lg 
            border-2 border-indigo-300 dark:border-indigo-700 
            hover:shadow-xl transition-shadow duration-300 
            overflow-hidden"
          >
            {/* Textarea Area - Top Section */}
            <div className="px-4 sm:px-6 pt-4 pb-2">
              <textarea
                ref={textareaRef}
                value={query}
                onChange={handleTextareaChange}
                disabled={isQuerying || !userId || isChatDisabled}
                placeholder={
                  !isServerOnline
                    ? "Server offline - Read only mode..."
                    : isLimitReached
                    ? "Daily query limit reached. Upgrade your plan or try again tomorrow..."
                    : isChatDisabled
                    ? "Upload a document first..."
                    : "Ask me anything..."
                }
                rows={1}
                className="w-full py-1 px-1 text-base bg-transparent focus:outline-none disabled:cursor-not-allowed transition-all duration-200 text-indigo-900 dark:text-indigo-50 placeholder-indigo-700 dark:placeholder-indigo-300 resize-none overflow-y-auto leading-6"
                style={{
                  minHeight: "44px",
                  maxHeight: "144px",
                  height: "44px",
                }}
                aria-label="Message input"
              />
            </div>

            {/* Action Buttons - Bottom Section */}
            <div className="flex items-center justify-between px-4 pb-4 sm:pb-4">
              {/* Left Action Buttons */}
              <div className="flex items-center gap-1">
                {/* Upload Button */}
                <button
                  type="button"
                  onClick={onOpenUploadModal}
                  disabled={!userId || !isServerOnline}
                  className="min-h-[44px] min-w-[44px] flex items-center justify-center h-10 w-10 rounded-full text-indigo-700 dark:text-indigo-200 hover:bg-indigo-100 dark:hover:bg-indigo-800 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 focus:outline-none focus:ring-3 focus:ring-focus"
                  title={
                    !isServerOnline
                      ? "Server offline - upload unavailable"
                      : "Upload document"
                  }
                  aria-label="Upload document"
                >
                  <Paperclip size={20} />
                </button>

                {/* Language Selector Button */}
                <button
                  type="button"
                  onClick={() => setIsLanguageSelectorOpen(true)}
                  disabled={!userId}
                  className="min-h-[44px] flex items-center justify-center h-10 px-3 rounded-full text-indigo-700 dark:text-indigo-200 hover:bg-indigo-100 dark:hover:bg-indigo-800 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 text-lg focus:outline-none focus:ring-3 focus:ring-focus"
                  title={`Response Language: ${selectedOutputLanguage.toUpperCase()}`}
                  aria-label="Select output language"
                >
                  {languageFlag}
                </button>
              </div>

              {/* Submit Button - Right Side */}
              <button
                type="submit"
                disabled={
                  isQuerying || !query.trim() || !userId || isChatDisabled
                }
                className={`min-h-[44px] min-w-[44px] flex items-center justify-center h-10 w-10 rounded-full transition-all duration-200 focus:outline-none focus:ring-3 focus:ring-focus ${
                  isQuerying || !query.trim() || !userId || isChatDisabled
                    ? "bg-indigo-300 dark:bg-indigo-700 text-indigo-700 dark:text-indigo-200 cursor-not-allowed"
                    : "bg-indigo-500 text-white hover:bg-indigo-700 shadow-md hover:shadow-lg"
                }`}
                title="Send message"
                aria-label="Send message"
              >
                {isQuerying ? (
                  <Loader size={20} className="animate-spin" />
                ) : (
                  <CornerDownLeft size={20} />
                )}
              </button>
            </div>
          </div>
        </div>
      </form>

      {/* Output Language Selector Modal */}
      <OutputLanguageSelector
        isOpen={isLanguageSelectorOpen}
        selectedLanguageCode={selectedOutputLanguage}
        onSelectLanguage={onSelectOutputLanguage}
        onClose={() => setIsLanguageSelectorOpen(false)}
      />
    </div>
  );
};
