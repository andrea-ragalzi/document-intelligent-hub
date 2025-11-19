import type { ChatMessage } from "@/lib/types";
import { MessageSquare, User as UserIcon, Loader } from "lucide-react";

interface ChatMessageDisplayProps {
  msg: ChatMessage;
}

// Utility function to clean [DOCUMENT X] markers from text
const cleanDocumentMarkers = (text: string): string => {
  return text.replace(/\s*\[DOCUMENT\s+\d+\]/gi, "");
};

export const ChatMessageDisplay: React.FC<ChatMessageDisplayProps> = ({
  msg,
}) => {
  const isUser = msg.type === "user";

  // Clean up the message text to remove [DOCUMENT X] markers
  const cleanedText = cleanDocumentMarkers(msg.text);

  return (
    <div
      className={`flex ${
        isUser ? "justify-end" : "justify-start"
      } mb-10 sm:mb-4 md:mb-10 px-1 sm:px-2`}
    >
      {!isUser && (
        <div className="flex-shrink-0 mr-2 sm:mr-3">
          <div className="w-7 h-7 sm:w-9 sm:h-9 rounded-full bg-blue-50 dark:bg-blue-900/30 flex items-center justify-center text-blue-600 dark:text-blue-400">
            <MessageSquare size={14} className="sm:size-4" />
          </div>
        </div>
      )}

      <div className="max-w-[85%] sm:max-w-[80%]">
        <div
          className={`p-3 sm:p-4 rounded-2xl sm:rounded-3xl shadow-lg transition duration-300 ${
            isUser
              ? "ml-auto bg-blue-600 text-white rounded-br-none"
              : "bg-white text-gray-800 rounded-tl-none border border-gray-100 dark:bg-gray-700 dark:text-gray-100 dark:border-gray-600"
          }`}
        >
          <div
            className={`flex items-center mb-1.5 sm:mb-2 font-semibold text-xs uppercase ${
              isUser ? "text-blue-200" : "text-gray-500 dark:text-gray-400"
            }`}
          >
            {isUser ? (
              <UserIcon size={10} className="mr-1.5 sm:mr-2 sm:size-3" />
            ) : (
              <MessageSquare
                size={10}
                className="mr-1.5 sm:mr-2 text-blue-600 dark:text-blue-400 sm:size-3"
              />
            )}
            {isUser ? "Tu" : "Assistente"}
          </div>

          {msg.isThinking ? (
            <div className="flex items-center text-xs sm:text-sm text-blue-500 dark:text-blue-300">
              <Loader size={14} className="animate-spin mr-2 sm:size-4" />
              <span className="italic">{cleanedText}</span>
            </div>
          ) : (
            <p className="whitespace-pre-wrap text-xs sm:text-sm leading-relaxed">
              {cleanedText}
            </p>
          )}

          {!isUser && msg.sources.length > 0 && !msg.isThinking && (
            <div className="mt-3 sm:mt-4 pt-2 sm:pt-3 border-t border-gray-200 dark:border-gray-600">
              <span className="text-xs font-bold text-blue-600 dark:text-blue-400 block mb-1">
                Fonti trovate ({msg.sources.length}):
              </span>
              <ul className="list-disc list-inside text-xs text-gray-600 dark:text-gray-300 space-y-0.5 max-h-20 sm:max-h-24 overflow-y-auto pr-2">
                {msg.sources.map((source, i) => (
                  <li key={i} className="truncate" title={source}>
                    {source}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>

      {isUser && (
        <div className="flex-shrink-0 ml-2 sm:ml-3">
          <div className="w-7 h-7 sm:w-9 sm:h-9 rounded-full bg-blue-600 flex items-center justify-center text-white">
            <UserIcon size={14} className="sm:size-4" />
          </div>
        </div>
      )}
    </div>
  );
};
