"use client";

import type { ChatMessage, ChatSource, SourceCitation } from "@/lib/types";
import { MessageSquare, User as UserIcon, Loader, Link as LinkIcon } from "lucide-react";
import { useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { API_BASE_URL } from "@/lib/constants";

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

const LEGACY_SOURCE_HEADINGS = new Set(["sources", "fonti", "fuentes", "quellen"]);

const splitLegacySources = (text: string): { answer: string; sources: string[] } => {
  const lines = text.split("\n");
  let lastContentLine = lines.length - 1;

  while (lastContentLine >= 0 && !lines[lastContentLine].trim()) {
    lastContentLine -= 1;
  }

  let firstSourceLine = lastContentLine;
  while (firstSourceLine >= 0 && lines[firstSourceLine].trimStart().startsWith("- ")) {
    firstSourceLine -= 1;
  }

  if (firstSourceLine === lastContentLine) return { answer: text, sources: [] };

  const heading = lines[firstSourceLine]?.trim() || "";
  const separatorIndex = heading.indexOf(":");
  const headingLabel = heading.slice(0, separatorIndex).replace("📚", "").trim().toLowerCase();
  const hasLegacyHeading =
    separatorIndex > 0 && heading.startsWith("📚") && LEGACY_SOURCE_HEADINGS.has(headingLabel);
  const hasBlankSeparator = firstSourceLine > 0 && !lines[firstSourceLine - 1].trim();

  if (!hasLegacyHeading || !hasBlankSeparator) return { answer: text, sources: [] };

  return {
    answer: lines
      .slice(0, firstSourceLine - 1)
      .join("\n")
      .trimEnd(),
    sources: lines
      .slice(firstSourceLine + 1, lastContentLine + 1)
      .map(line => line.replace(/^\s*-\s+/, "").trim())
      .filter(Boolean),
  };
};

const normalizeSourceCitation = (source: ChatSource): SourceCitation =>
  typeof source === "string" ? { filename: source } : source;

const deduplicateCitations = (sources: ChatSource[]): SourceCitation[] => {
  const seen = new Set<string>();
  return sources
    .map(normalizeSourceCitation)
    .filter(source => {
      const key = `${source.filename}:${source.page_number ?? ""}`;
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    })
    .slice(0, 5);
};

const formatCitation = (citation: SourceCitation): string =>
  citation.page_number ? `${citation.filename} — p. ${citation.page_number}` : citation.filename;

const BLOB_URL_REVOKE_DELAY_MS = 60_000;

const Avatar: React.FC<{ isUser: boolean }> = ({ isUser }) => (
  <div
    className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-white transition-colors duration-200 ${
      isUser ? "bg-accent text-on-accent" : "bg-raised text-muted"
    } ${isUser ? "ml-2" : "mr-2"}`}
  >
    {isUser ? <UserIcon size={16} /> : <MessageSquare size={16} />}
  </div>
);

const CitationSources: React.FC<{ sources: SourceCitation[] }> = ({ sources }) => {
  const { getIdToken } = useAuth();
  const [citationError, setCitationError] = useState<string | null>(null);

  const openCitation = async (citation: SourceCitation) => {
    setCitationError(null);
    const previewWindow = window.open("about:blank", "_blank");
    if (!previewWindow) {
      setCitationError("Allow pop-ups to open this document.");
      return;
    }

    try {
      previewWindow.opener = null;
      const token = await getIdToken();
      if (!token) throw new Error("Missing authentication token");

      const query = new URLSearchParams({ filename: citation.filename });
      const response = await fetch(`${API_BASE_URL}/documents/content?${query.toString()}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) throw new Error("Document content request failed");

      const blobUrl = URL.createObjectURL(await response.blob());
      previewWindow.location.href = `${blobUrl}#page=${citation.page_number || 1}`;
      window.setTimeout(() => URL.revokeObjectURL(blobUrl), BLOB_URL_REVOKE_DELAY_MS);
    } catch {
      previewWindow.close();
      setCitationError("Unable to open this document.");
    }
  };

  return (
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
          <li key={`${source.filename}:${source.page_number ?? ""}`}>
            <button
              type="button"
              onClick={() => void openCitation(source)}
              className="block w-full truncate text-left underline decoration-line/40 underline-offset-2 transition-colors hover:text-accent focus:outline-none focus:ring-2 focus:ring-accent/70 focus:ring-offset-2 focus:ring-offset-raised"
              title={`Open ${formatCitation(source)}`}
            >
              {formatCitation(source)}
            </button>
          </li>
        ))}
      </ul>
      {citationError && (
        <p role="alert" className="mt-2 text-xs text-danger">
          {citationError}
        </p>
      )}
    </section>
  );
};

export const ChatMessageDisplay: React.FC<ChatMessageDisplayProps> = ({ msg }) => {
  const isUser = msg.type === "user";

  const { answer, sources: legacySources } = splitLegacySources(msg.text);
  const cleanedText = cleanDocumentMarkers(answer);
  const sources = deduplicateCitations([...msg.sources, ...legacySources]);

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

        {!isUser && sources.length > 0 && !msg.isThinking && <CitationSources sources={sources} />}
      </div>

      {isUser && <Avatar isUser={true} />}
    </div>
  );
};
