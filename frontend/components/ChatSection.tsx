import { FormEvent } from "react";
import type { ChatMessage } from "@/lib/types";
import { ChatMessageDisplay } from "./ChatMessageDisplay";
import { OutputLanguageSelector } from "./OutputLanguageSelector";
import { useChatScroll } from "./ChatSection/useChatScroll";
import { useTextareaResize } from "./ChatSection/useTextareaResize";
import { useLanguageFlag } from "./ChatSection/useLanguageFlag";
import {
  getChatDisabledState,
  createSubmitHandler,
  shouldShowChatLoadingSkeleton,
} from "./ChatSection/chatHelpers";
import { ChatEmptyState } from "./ChatSection/ChatEmptyState";
import { getPlaceholderText } from "./ChatSection/placeholderText";
import { ChatLoadingSkeleton } from "./ChatSection/ChatLoadingSkeleton";
import { ChatInputActions } from "./ChatSection/ChatInputActions";
import type { DemoDocumentState } from "@/hooks/useDemoDocument";

interface ChatSectionProps {
  chatHistory: ChatMessage[];
  query: string;
  isQuerying: boolean;
  userId: string | null;
  onQueryChange: (value: string) => void;
  onQuerySubmit: (e: FormEvent) => void;
  hasDocuments: boolean;
  isCheckingDocuments: boolean;
  onOpenUploadModal: () => void;
  selectedOutputLanguage: string;
  onSelectOutputLanguage: (code: string) => void;
  isServerOnline?: boolean;
  isLimitReached?: boolean;
  demoDocumentState: DemoDocumentState;
  suggestedQuestions: string[];
  onSuggestedQuestion: (question: string) => void;
}
export const ChatSection: React.FC<ChatSectionProps> = ({
  chatHistory,
  query,
  isQuerying,
  userId,
  onQueryChange,
  onQuerySubmit,
  hasDocuments,
  isCheckingDocuments,
  onOpenUploadModal,
  selectedOutputLanguage,
  onSelectOutputLanguage,
  isServerOnline = true,
  isLimitReached = false,
  demoDocumentState,
  suggestedQuestions,
  onSuggestedQuestion,
}) => {
  const chatEndRef = useChatScroll(chatHistory, isQuerying);
  const { textareaRef, resetHeight, handleChange } = useTextareaResize();
  const { isLanguageSelectorOpen, setIsLanguageSelectorOpen, languageFlag } =
    useLanguageFlag(selectedOutputLanguage);

  // Calculate specific disable reasons
  const { isChatDisabled, noDocuments } = getChatDisabledState(
    hasDocuments,
    isCheckingDocuments,
    isServerOnline,
    isLimitReached
  );

  // Handle form submission with textarea reset
  const handleSubmit = createSubmitHandler(
    query,
    isQuerying,
    userId,
    isChatDisabled,
    onQuerySubmit,
    resetHeight
  );

  return (
    <div className="relative flex h-full min-h-0 w-full flex-col bg-canvas pb-0 font-[Inter] transition-colors duration-200 ease-in-out">
      {/* The message list owns scrolling; the composer remains in the flex flow. */}
      <div className="min-h-0 w-full flex-1 overflow-y-auto p-4 pb-0 sm:p-6 sm:pb-0">
        <div className="max-w-4xl mx-auto">
          {chatHistory.length === 0 ? (
            <div className="text-center p-8 sm:p-16 text-muted">
              <ChatEmptyState
                isCheckingDocuments={isCheckingDocuments}
                isServerOnline={isServerOnline}
                isLimitReached={isLimitReached}
                noDocuments={noDocuments}
                demoDocumentState={demoDocumentState}
                suggestedQuestions={suggestedQuestions}
                onSelectQuestion={onSuggestedQuestion}
                onOpenUpload={onOpenUploadModal}
              />
            </div>
          ) : (
            // Display history and optional skeleton loader
            <>
              {chatHistory.map((msg, index) => (
                <ChatMessageDisplay key={`${msg.type}-${index}`} msg={msg} />
              ))}
              <ChatLoadingSkeleton
                isQuerying={shouldShowChatLoadingSkeleton(chatHistory, isQuerying)}
              />
            </>
          )}
          <div ref={chatEndRef} />
        </div>
      </div>

      {/* Gemini-style input bar. Safe-area padding keeps controls above mobile browser UI. */}
      <form
        onSubmit={handleSubmit}
        className="z-10 shrink-0 bg-transparent px-4 pt-2 pb-[max(0.75rem,env(safe-area-inset-bottom))] transition-all duration-200 ease-in-out md:px-4 md:pt-4 md:pb-3"
      >
        <div className="max-w-4xl md:mx-auto">
          {/* Gemini-inspired Input Container */}
          <div
            className="relative bg-surface
            rounded-3xl md:rounded-[32px]
            border border-line/20
            shadow-sm hover:border-line/35 transition-colors duration-300
            overflow-hidden"
          >
            {/* Textarea Area - Top Section */}
            <div className="px-4 sm:px-6 pt-4 pb-2">
              <textarea
                ref={textareaRef}
                value={query}
                onChange={e => handleChange(e, onQueryChange)}
                disabled={isQuerying || !userId || isChatDisabled}
                placeholder={getPlaceholderText(isServerOnline, isLimitReached, isChatDisabled)}
                rows={1}
                className="w-full py-1 px-1 text-base bg-transparent focus:outline-none disabled:cursor-not-allowed transition-all duration-200 text-ink placeholder-quiet resize-none overflow-y-auto leading-6"
                style={{
                  minHeight: "44px",
                  maxHeight: "144px",
                  height: "44px",
                }}
                aria-label="Message input"
              />
            </div>

            {/* Action Buttons - Bottom Section */}
            <ChatInputActions
              userId={userId}
              isServerOnline={isServerOnline}
              isQuerying={isQuerying}
              query={query}
              isChatDisabled={isChatDisabled}
              languageFlag={languageFlag}
              selectedOutputLanguage={selectedOutputLanguage}
              onOpenUploadModal={onOpenUploadModal}
              onOpenLanguageSelector={() => setIsLanguageSelectorOpen(true)}
            />
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
