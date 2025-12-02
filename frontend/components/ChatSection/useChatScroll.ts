/**
 * Custom hook for chat scroll behavior
 */

import { useEffect, useRef } from "react";

export function useChatScroll(chatHistory: unknown[], isQuerying: boolean) {
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const scrollToBottom = () => {
      if (chatEndRef.current) {
        chatEndRef.current.scrollIntoView({ behavior: "smooth", block: "end" });
      }
    };

    // Small delay to ensure DOM is updated
    const timeoutId = setTimeout(scrollToBottom, 100);
    return () => clearTimeout(timeoutId);
  }, [chatHistory, isQuerying]);

  return chatEndRef;
}
