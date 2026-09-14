/**
 * Custom hook for chat scroll behavior
 */

import { useEffect, useRef } from "react";

export function useChatScroll(chatHistory: unknown[], isQuerying: boolean) {
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Do not scroll the page to the empty-state sentinel on initial mobile load.
    // The composer is already visible; scrolling the sentinel can move it below
    // the browser viewport before the user interacts with the chat.
    if (chatHistory.length === 0 && !isQuerying) return;

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
