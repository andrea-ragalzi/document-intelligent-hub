/**
 * Custom hook for chat scroll behavior
 */

import { useEffect, useRef } from "react";

export function useChatScroll(chatHistory: unknown[], isQuerying: boolean) {
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const animationFrameId = requestAnimationFrame(() => {
      if (chatEndRef.current) {
        chatEndRef.current.scrollIntoView({
          behavior: isQuerying ? "auto" : "smooth",
          block: "end",
        });
      }
    });

    return () => cancelAnimationFrame(animationFrameId);
  }, [chatHistory, isQuerying]);

  return chatEndRef;
}
