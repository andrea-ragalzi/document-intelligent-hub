import type { ChatMessage } from "@/lib/types";
import { MessageSquare, User as UserIcon, Loader, Link as LinkIcon } from "lucide-react";

interface ChatMessageDisplayProps {
  msg: ChatMessage;
}

// Utility function to clean [DOCUMENT X] markers from text
// Regex is safe: no quantifier nesting, linear time complexity
const cleanDocumentMarkers = (text: string): string => {
  // Match [DOCUMENT <number>] with optional leading space
  // Using \d+ is safe here as it's not nested and digits are bounded
  return text.replaceAll(/\s?\[DOCUMENT \d+\]/gi, "");
};

const Avatar: React.FC<{ isUser: boolean }> = ({ isUser }) => (
  <div
    className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-white transition-colors duration-200 ${
      isUser ? "bg-accent text-on-accent" : "bg-raised text-muted"
    } ${isUser ? "ml-2" : "mr-2"}`}
  >
    {isUser ? <UserIcon size={16} /> : <MessageSquare size={16} />}
  </div>
);

export const ChatMessageDisplay: React.FC<ChatMessageDisplayProps> = ({ msg }) => {
  const isUser = msg.type === "user";

  // Clean up the message text to remove [DOCUMENT X] markers
  const cleanedText = cleanDocumentMarkers(msg.text);

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4 sm:mb-6 px-1 sm:px-2`}>
      {!isUser && <Avatar isUser={false} />}

      <div className="max-w-[85%] sm:max-w-[80%] flex flex-col">
        {/* Message author */}
        <div
          className={`text-xs font-medium mb-1 ${
            isUser ? "text-muted text-right pr-2" : "text-muted pl-2"
          }`}
        >
          {isUser ? "You" : "Assistant"}
        </div>

        {/* Message content */}
        <div
          className={`p-3 sm:p-4 rounded-xl border border-line/15 transition duration-300 break-words overflow-wrap-anywhere ${
            isUser
              ? "ml-auto bg-accent text-on-accent rounded-br-sm"
              : "bg-surface text-ink rounded-tl-sm"
          }`}
        >
          {msg.isThinking ? (
            <div className="flex items-center text-sm italic opacity-80">
              <Loader size={16} className="animate-spin mr-2" />
              <span className="break-words">{cleanedText}</span>
            </div>
          ) : (
            <p className="whitespace-pre-wrap text-sm leading-relaxed break-words">{cleanedText}</p>
          )}

          {/* Sources */}
          {!isUser && msg.sources.length > 0 && !msg.isThinking && (
            <div className="mt-3 pt-2 border-t border-line/15">
              <span className="text-xs font-semibold text-muted flex items-center mb-1">
                <LinkIcon size={12} className="mr-1.5" />
                Sources ({msg.sources.length}):
              </span>
              <ul className="list-disc list-inside text-xs text-ink space-y-0.5 max-h-24 overflow-y-auto pr-2">
                {msg.sources.map((source, i) => (
                  <li
                    key={`source-${i}-${source.substring(0, 30)}`}
                    className="truncate hover:text-accent transition-colors"
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
