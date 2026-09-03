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

const LEGACY_SOURCES_BLOCK =
  /\n{2}📚\s+(?:Sources|Fonti|Fuentes|Quellen):\s*\n((?:-\s+[^\n]+\n?)+)\s*$/i;

const splitLegacySources = (text: string): { answer: string; sources: string[] } => {
  const match = text.match(LEGACY_SOURCES_BLOCK);
  if (!match) return { answer: text, sources: [] };

  return {
    answer: text.slice(0, match.index).trimEnd(),
    sources: match[1]
      .split("\n")
      .map(line => line.replace(/^\s*-\s+/, "").trim())
      .filter(Boolean),
  };
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

  const { answer, sources: legacySources } = splitLegacySources(msg.text);
  const cleanedText = cleanDocumentMarkers(answer);
  const sources = [...new Set([...msg.sources, ...legacySources])];

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

        </div>

        {!isUser && sources.length > 0 && !msg.isThinking && (
          <section
            aria-label="Sources"
            className="mt-2 rounded-lg border border-line/15 bg-raised/50 px-3 py-2"
          >
            <h3 className="mb-1 flex items-center text-xs font-semibold text-muted">
              <LinkIcon size={12} className="mr-1.5" />
              Sources
            </h3>
            <ul className="max-h-24 space-y-0.5 overflow-y-auto pr-2 text-xs text-ink">
              {sources.map(source => (
                <li key={source} className="truncate" title={source}>
                  {source}
                </li>
              ))}
            </ul>
          </section>
        )}
      </div>

      {isUser && <Avatar isUser={true} />}
    </div>
  );
};
