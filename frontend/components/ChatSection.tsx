import { FormEvent } from "react";
import {
  MessageSquare,
  CornerDownLeft,
  Loader,
  PlusCircle,
} from "lucide-react";
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
  onNewConversation: () => void;
  hasDocuments: boolean;
  isCheckingDocuments: boolean;
}
export const ChatSection: React.FC<ChatSectionProps> = ({
  chatHistory,
  query,
  isQuerying,
  userId,
  chatEndRef,
  onQueryChange,
  onQuerySubmit,
  onNewConversation,
  hasDocuments,
  isCheckingDocuments,
}) => {
  const isChatDisabled = !hasDocuments && !isCheckingDocuments;
  return (
    <div className="lg:w-2/3 flex flex-col bg-white dark:bg-gray-800 rounded-2xl shadow-xl transition-colors duration-500">
      <header className="p-5 border-b border-gray-100 dark:border-gray-700 bg-gray-50 dark:bg-gray-700/50 rounded-t-2xl flex justify-between items-center">
        <h2 className="text-xl font-bold text-gray-800 dark:text-white flex items-center">
          <MessageSquare size={20} className="mr-2 text-blue-600" />
          RAG Chat Assistant
        </h2>
        <button
          onClick={onNewConversation}
          disabled={chatHistory.length === 0}
          title="New conversation"
          className="px-3 py-2 rounded-lg bg-gray-200 text-gray-700 hover:bg-gray-300 dark:bg-gray-600 dark:text-gray-200 dark:hover:bg-gray-500 disabled:opacity-50 disabled:cursor-not-allowed transition flex items-center gap-2 text-sm font-medium"
        >
          <PlusCircle size={16} />
          New
        </button>
      </header>
      <div className="flex-grow p-6 overflow-y-auto h-[70vh] min-h-[400px] bg-gray-50 dark:bg-gray-900/50">
        {chatHistory.length === 0 ? (
          <div className="text-center p-12 text-gray-400">
            <MessageSquare size={64} className="mx-auto mb-4 text-blue-200" />
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
        className="p-4 border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 rounded-b-2xl"
      >
        <div className="flex items-center space-x-3">
          <input
            type="text"
            value={query}
            onChange={(e) => onQueryChange(e.target.value)}
            disabled={isQuerying || !userId || isChatDisabled}
            placeholder={
              isChatDisabled
                ? "Upload a document first..."
                : "Type your question here..."
            }
            className="flex-grow p-3 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500 shadow-inner disabled:bg-gray-100 transition text-sm
              bg-white dark:bg-gray-900 dark:border-gray-600 dark:text-white disabled:dark:bg-gray-700"
          />
          <button
            type="submit"
            disabled={isQuerying || !query.trim() || !userId || isChatDisabled}
            className={`flex items-center justify-center p-3 rounded-lg shadow-md transition duration-200 ${
              isQuerying || !query.trim() || !userId || isChatDisabled
                ? "bg-gray-300 text-gray-600 cursor-not-allowed dark:bg-gray-600 dark:text-gray-300"
                : "bg-blue-600 text-white hover:bg-blue-700 hover:shadow-lg"
            }`}
          >
            {isQuerying ? (
              <Loader size={20} className="animate-spin" />
            ) : (
              <CornerDownLeft size={20} />
            )}
          </button>
        </div>
      </form>
    </div>
  );
};
