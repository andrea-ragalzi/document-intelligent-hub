import { useChat } from "ai/react";
import type { Message } from "ai/react";
import { ChatMessage } from "@/lib/types";
import { useAuth } from "@/contexts/AuthContext";
import { useEffect, useState } from "react";

interface UseChatAIProps {
  userId: string;
  selectedOutputLanguage?: string;
}

export function useChatAI({ userId, selectedOutputLanguage }: UseChatAIProps) {
  const { getIdToken } = useAuth();
  const [authToken, setAuthToken] = useState<string | null>(null);

  // Get auth token on mount
  useEffect(() => {
    const fetchToken = async () => {
      const token = await getIdToken();
      setAuthToken(token);
    };
    fetchToken();
  }, [getIdToken]);

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
    headers: authToken
      ? {
          Authorization: `Bearer ${authToken}`,
        }
      : undefined,
    body: {
      userId,
      output_language: selectedOutputLanguage?.toUpperCase(),
    },
    onError: (error: Error) => {
      // Silently handle rate limit errors (429) - they're expected
      if (error.message.includes("Daily query limit exceeded")) {
        console.log("⚠️ Query limit reached");
      } else {
        console.error("Chat error:", error);
      }
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
