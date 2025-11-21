import type { ChatMessage } from "@/lib/types";
import {
  MessageSquare,
  User as UserIcon,
  Loader,
  Link as LinkIcon,
} from "lucide-react";

interface ChatMessageDisplayProps {
  msg: ChatMessage;
}

// Utility function to clean [DOCUMENT X] markers from text
const cleanDocumentMarkers = (text: string): string => {
  return text.replace(/\s*\[DOCUMENT\s+\d+\]/gi, "");
};

// Componente di visualizzazione dell'Avatar
const Avatar: React.FC<{ isUser: boolean }> = ({ isUser }) => (
  <div
    className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-white transition-colors duration-200 ${
      isUser
        ? "bg-indigo-600 dark:bg-indigo-500" // Utente: colore primario
        : "bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300" // Assistente: colore secondario/neutro
    } ${isUser ? "ml-2" : "mr-2"}`}
  >
    {isUser ? <UserIcon size={16} /> : <MessageSquare size={16} />}
  </div>
);

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
      } mb-4 sm:mb-6 px-1 sm:px-2`}
    >
      {!isUser && <Avatar isUser={false} />}

      <div className="max-w-[85%] sm:max-w-[80%] flex flex-col">
        {/* Header (Nome Utente/Assistente) */}
        <div
          className={`text-xs font-medium mb-1 ${
            isUser
              ? "text-gray-500 dark:text-gray-400 text-right pr-2"
              : "text-indigo-600 dark:text-indigo-400 pl-2"
          }`}
        >
          {isUser ? "Tu" : "Assistente"}
        </div>

        {/* Bubble Messaggio */}
        <div
          className={`p-3 sm:p-4 rounded-xl shadow-md transition duration-300 break-words overflow-wrap-anywhere ${
            isUser
              ? "ml-auto bg-indigo-600 text-white rounded-br-sm" // Utente: colore primario, angolo inferiore-destro piccolo
              : "bg-white text-gray-800 rounded-tl-sm border border-gray-100 dark:bg-gray-800 dark:text-gray-100 dark:border-gray-700" // Assistente: colore chiaro, angolo superiore-sinistro piccolo
          }`}
        >
          {msg.isThinking ? (
            <div className="flex items-center text-sm italic opacity-80">
              <Loader size={16} className="animate-spin mr-2" />
              <span className="break-words">{cleanedText}</span>
            </div>
          ) : (
            <p className="whitespace-pre-wrap text-sm leading-relaxed break-words">
              {cleanedText}
            </p>
          )}

          {/* Source/Citations Section (Solo per l'Assistente e quando non sta pensando) */}
          {!isUser && msg.sources.length > 0 && !msg.isThinking && (
            <div className="mt-3 pt-2 border-t border-gray-200 dark:border-gray-700">
              <span className="text-xs font-semibold text-gray-500 dark:text-gray-400 flex items-center mb-1">
                <LinkIcon size={12} className="mr-1.5" />
                Fonti trovate ({msg.sources.length}):
              </span>
              <ul className="list-disc list-inside text-xs text-gray-600 dark:text-gray-300 space-y-0.5 max-h-24 overflow-y-auto pr-2">
                {msg.sources.map((source, i) => (
                  <li
                    key={i}
                    className="truncate hover:text-indigo-500 transition-colors"
                  >
                    <a
                      href={source}
                      target="_blank"
                      rel="noopener noreferrer"
                      title={source}
                      className="underline-offset-2 hover:underline"
                    >
                      {source}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>

      {isUser && <Avatar isUser={true} />}
    </div>
  );
};
