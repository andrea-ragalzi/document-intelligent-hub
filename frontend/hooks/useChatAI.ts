import { useChat } from "ai/react";
import type { Message } from "ai/react";
import { ChatMessage } from "@/lib/types";

interface UseChatAIProps {
  userId: string;
  selectedOutputLanguage?: string;
}

export function useChatAI({ userId, selectedOutputLanguage }: UseChatAIProps) {
  // Log output language selection
  console.log(
    `🌍 [useChatAI] Output language: ${selectedOutputLanguage || "auto"}`
  );

  const {
    messages,
    input,
    handleInputChange,
    handleSubmit,
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
      console.error("Chat error:", error);
    },
  });

  // Converti i messaggi dal formato Vercel AI al formato ChatMessage
  const chatHistory: ChatMessage[] = messages
    .filter((msg) => msg.role !== "data")
    .map((msg: Message) => ({
      type: msg.role === "user" ? ("user" as const) : ("assistant" as const),
      text: msg.content,
      sources: [], // Le fonti verranno gestite diversamente con lo streaming
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
