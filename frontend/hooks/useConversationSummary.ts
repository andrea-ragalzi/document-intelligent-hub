"use client";

import { useEffect, useRef } from "react";
import type { ChatMessage } from "@/lib/types";
import { API_BASE_URL } from "@/lib/constants";

interface UseConversationSummaryProps {
  chatHistory: ChatMessage[];
  conversationId: string | null;
  onSummaryGenerated?: (summary: string) => void;
}

const SUMMARIZE_THRESHOLD = 20; // Trigger summarization every 20 messages

/**
 * Hook to automatically generate conversation summaries for long-term memory.
 * Triggers when conversation reaches certain message thresholds.
 */
export const useConversationSummary = ({
  chatHistory,
  conversationId,
  onSummaryGenerated,
}: UseConversationSummaryProps) => {
  const lastSummarizedCountRef = useRef(0);
  const isSummarizingRef = useRef(false);

  useEffect(() => {
    // Don't summarize if:
    // - No conversation ID (not saved yet)
    // - Already summarizing
    // - Not enough messages since last summary
    if (
      !conversationId ||
      isSummarizingRef.current ||
      chatHistory.length < SUMMARIZE_THRESHOLD ||
      chatHistory.length - lastSummarizedCountRef.current < SUMMARIZE_THRESHOLD
    ) {
      return;
    }

    const generateSummary = async () => {
      isSummarizingRef.current = true;
      console.log(
        `🧠 Generating conversation summary (${chatHistory.length} messages)`
      );

      try {
        // Prepare conversation history for summarization
        const conversationHistory = chatHistory
          .filter((msg) => !msg.isThinking)
          .map((msg) => ({
            role: msg.type === "user" ? "user" : "assistant",
            content: msg.text,
          }));

        const response = await fetch(`${API_BASE_URL}/summarize/`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            conversation_history: conversationHistory,
          }),
        });

        if (response.ok) {
          const data = await response.json();
          console.log(
            `✅ Summary generated: ${data.summary.substring(0, 100)}...`
          );

          lastSummarizedCountRef.current = chatHistory.length;

          if (onSummaryGenerated) {
            onSummaryGenerated(data.summary);
          }
        } else {
          console.error("Failed to generate summary:", response.statusText);
        }
      } catch (error) {
        console.error("Error generating conversation summary:", error);
      } finally {
        isSummarizingRef.current = false;
      }
    };

    // Debounce: wait 2 seconds after last message before summarizing
    const timeoutId = setTimeout(generateSummary, 2000);

    return () => clearTimeout(timeoutId);
  }, [chatHistory, conversationId, onSummaryGenerated]);

  return {
    lastSummarizedCount: lastSummarizedCountRef.current,
    summarizeThreshold: SUMMARIZE_THRESHOLD,
  };
};
