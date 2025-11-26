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
// Regex is safe: no nested quantifiers, bounded input from backend
const cleanDocumentMarkers = (text: string): string => {
  // Match [DOCUMENT <number>] with optional leading space (no backtracking risk)
  return text.replaceAll(/\s?\[DOCUMENT\s+\d+\]/gi, "");
};

// Componente di visualizzazione dell'Avatar
const Avatar: React.FC<{ isUser: boolean }> = ({ isUser }) => (
  <div
    className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-white transition-colors duration-200 ${
      isUser
        ? "bg-indigo-500" // Utente: colore primario
        : "bg-indigo-300 dark:bg-indigo-700 text-indigo-900 dark:text-indigo-50" // Assistente: colore secondario/neutro
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
              ? "text-indigo-700 dark:text-indigo-200 text-right pr-2"
              : "text-indigo-700 dark:text-indigo-200 pl-2"
          }`}
        >
          {isUser ? "Tu" : "Assistente"}
        </div>

        {/* Bubble Messaggio */}
        <div
          className={`p-3 sm:p-4 rounded-xl shadow-md transition duration-300 break-words overflow-wrap-anywhere ${
            isUser
              ? "ml-auto bg-indigo-500 text-white rounded-br-sm" // Utente: colore primario, angolo inferiore-destro piccolo
              : "bg-white text-indigo-900 rounded-tl-sm border-2 border-indigo-100 dark:bg-indigo-950 dark:text-indigo-50 dark:border-indigo-800" // Assistente: colore chiaro, angolo superiore-sinistro piccolo
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
            <div className="mt-3 pt-2 border-t border-indigo-300 dark:border-indigo-700">
              <span className="text-xs font-semibold text-indigo-700 dark:text-indigo-200 flex items-center mb-1">
                <LinkIcon size={12} className="mr-1.5" />
                Fonti trovate ({msg.sources.length}):
              </span>
              <ul className="list-disc list-inside text-xs text-indigo-900 dark:text-indigo-50 space-y-0.5 max-h-24 overflow-y-auto pr-2">
                {msg.sources.map((source, i) => (
                  <li
                    key={`source-${i}-${source.substring(0, 30)}`}
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
