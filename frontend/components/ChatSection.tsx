import { FormEvent } from "react";
import { MessageSquare } from "lucide-react";
import type { ChatMessage } from "@/lib/types";
import { ChatMessageDisplay } from "./ChatMessageDisplay";
import { OutputLanguageSelector } from "./OutputLanguageSelector";
import { useChatScroll } from "./ChatSection/useChatScroll";
import { useTextareaResize } from "./ChatSection/useTextareaResize";
import { useLanguageFlag } from "./ChatSection/useLanguageFlag";
import { getChatDisabledState, createSubmitHandler } from "./ChatSection/chatHelpers";
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
    <div className="w-full h-full flex flex-col bg-canvas transition-colors duration-200 ease-in-out font-[Inter] relative pb-0">
      {/* Scrollable Chat Area: Altezza calcolata per lasciare spazio all'input bar */}
      <div
        className="p-4 sm:p-6 overflow-y-auto w-full flex-grow pb-0"
        // Adjust height to allow for the sticky input bar (approx 100px height for the bar)
        style={{ height: "calc(100vh - 100px)" }}
      >
        <div className="max-w-4xl mx-auto">
          {chatHistory.length === 0 ? (
            <div className="text-center p-8 sm:p-16 text-muted">
              <MessageSquare size={48} className="sm:size-16 mx-auto mb-4 text-quiet" />
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
              {chatHistory.map(msg => (
                <ChatMessageDisplay key={`${msg.type}-${msg.text}`} msg={msg} />
              ))}
              <ChatLoadingSkeleton isQuerying={isQuerying} />
            </>
          )}
          <div ref={chatEndRef} />
        </div>
      </div>

      {/* Gemini-style Input Bar - Sticky bottom with elegant spacing */}
      <form
        onSubmit={handleSubmit}
        className="sticky bottom-0 left-0 right-0 bg-transparent pt-0 pb-0 -mx-4 md:mx-0 md:pt-4 md:pb-3 md:px-4 transition-all duration-200 ease-in-out z-10"
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
