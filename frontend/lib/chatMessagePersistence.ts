import type { Message } from "ai/react";
import type { ChatMessage, ChatSource } from "./types";

type PersistedChatMessage = Omit<ChatMessage, "sources"> & {
  sources?: ChatSource[];
};

const toSourceAnnotations = (sources: ChatSource[] | undefined): Message["annotations"] => {
  if (!sources?.length) return undefined;

  const serializableSources = sources.map(source =>
    typeof source === "string"
      ? source
      : {
          filename: source.filename,
          ...(typeof source.page_number === "number" ? { page_number: source.page_number } : {}),
        }
  );

  return [{ type: "sources", sources: serializableSources }] as Message["annotations"];
};

/**
 * Restore Firestore's persisted source metadata to the annotations read by useChatAI.
 * Older conversations can omit `sources` and continue to load as plain messages.
 */
export const toAiSdkMessages = (
  conversationId: string,
  history: PersistedChatMessage[]
): Message[] =>
  history.map((message, index) => ({
    id: `loaded-${conversationId}-${index}`,
    role: message.type === "user" ? "user" : "assistant",
    content: message.text,
    ...(message.type === "assistant" ? { annotations: toSourceAnnotations(message.sources) } : {}),
  }));
