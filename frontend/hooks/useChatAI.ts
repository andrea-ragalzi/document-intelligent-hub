import { useChat } from "ai/react";
import type { Message } from "ai/react";
import { ChatMessage, SourceCitation } from "@/lib/types";
import { useAuth } from "@/contexts/AuthContext";

interface UseChatAIProps {
  userId: string;
  selectedOutputLanguage?: string;
}

const getSourceCitations = (annotations: Message["annotations"]): SourceCitation[] => {
  const sourcesAnnotation = annotations?.find(
    annotation =>
      typeof annotation === "object" &&
      annotation !== null &&
      !Array.isArray(annotation) &&
      "type" in annotation &&
      annotation.type === "sources" &&
      "sources" in annotation
  );

  if (
    !sourcesAnnotation ||
    typeof sourcesAnnotation !== "object" ||
    Array.isArray(sourcesAnnotation) ||
    !Array.isArray(sourcesAnnotation.sources)
  ) {
    return [];
  }

  return sourcesAnnotation.sources.flatMap((source): SourceCitation[] => {
    if (typeof source === "string") return [{ filename: source }];
    if (
      typeof source !== "object" ||
      source === null ||
      Array.isArray(source) ||
      !("filename" in source) ||
      typeof source.filename !== "string"
    ) {
      return [];
    }
    if (
      "page_number" in source &&
      source.page_number !== undefined &&
      (typeof source.page_number !== "number" || source.page_number <= 0)
    ) {
      return [];
    }
    return [
      {
        filename: source.filename,
        ...(typeof source.page_number === "number" ? { page_number: source.page_number } : {}),
      },
    ];
  });
};

export function useChatAI({ userId, selectedOutputLanguage }: UseChatAIProps) {
  const { getIdToken } = useAuth();

  const {
    messages,
    input,
    handleInputChange,
    handleSubmit: submitChat,
    isLoading,
    error,
    setMessages,
  } = useChat({
    api: "/api/chat",
    body: {
      userId,
      output_language: selectedOutputLanguage?.toUpperCase(),
    },
    onError: (error: Error) => {
      // Silently handle rate limit errors (429) - they're expected
      if (error.message.includes("Daily query limit exceeded")) {
        return;
      } else {
        console.error("Chat error:", error);
      }
    },
  });

  // Firebase ID tokens expire after a session has been open for a while. Resolve
  // the token for every request so Firebase can refresh it before the chat call.
  const handleSubmit = async (event?: { preventDefault?: () => void }) => {
    event?.preventDefault?.();

    const token = await getIdToken();
    if (!token) {
      console.error("Chat error: no authenticated Firebase token available");
      return;
    }

    submitChat(undefined, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  };

  // Converti i messaggi dal formato Vercel AI al formato ChatMessage
  const chatHistory: ChatMessage[] = messages
    .filter(msg => msg.role !== "data")
    .map((msg: Message) => ({
      type: msg.role === "user" ? ("user" as const) : ("assistant" as const),
      text: msg.content,
      sources: msg.role === "assistant" ? getSourceCitations(msg.annotations) : [],
    }));

  return {
    chatHistory,
    input,
    handleInputChange,
    handleSubmit,
    isLoading,
    error,
    setMessages,
  };
}
