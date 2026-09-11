/**
 * Helper functions for chat form submission
 */

import { FormEvent } from "react";
import type { ChatMessage } from "@/lib/types";

export const MAX_QUERY_LENGTH = 1000;

/** Show the placeholder only until the current assistant response begins streaming. */
export function shouldShowChatLoadingSkeleton(
  chatHistory: ChatMessage[],
  isQuerying: boolean
): boolean {
  return isQuerying && chatHistory.at(-1)?.type !== "assistant";
}

/**
 * Checks if chat is disabled and returns reason
 */
export function getChatDisabledState(
  hasDocuments: boolean,
  isCheckingDocuments: boolean,
  isServerOnline: boolean,
  isLimitReached: boolean
): { isChatDisabled: boolean; noDocuments: boolean } {
  const noDocuments = !hasDocuments && !isCheckingDocuments;
  const isChatDisabled = noDocuments || !isServerOnline || isLimitReached;

  return { isChatDisabled, noDocuments };
}

/**
 * Checks if form submission should be allowed
 */
export function canSubmitQuery(
  query: string,
  isQuerying: boolean,
  userId: string | null,
  isChatDisabled: boolean
): boolean {
  return Boolean(
    query.trim() && query.length <= MAX_QUERY_LENGTH && !isQuerying && userId && !isChatDisabled
  );
}

/**
 * Creates form submit handler with textarea reset
 */
export function createSubmitHandler(
  query: string,
  isQuerying: boolean,
  userId: string | null,
  isChatDisabled: boolean,
  onQuerySubmit: (e: FormEvent) => void,
  resetTextareaHeight: () => void,
  onQueryTooLong?: () => void
) {
  return (e: FormEvent) => {
    e.preventDefault();

    if (query.length > MAX_QUERY_LENGTH) {
      onQueryTooLong?.();
      return;
    }

    if (!canSubmitQuery(query, isQuerying, userId, isChatDisabled)) {
      return;
    }

    onQuerySubmit(e);
    resetTextareaHeight();
  };
}
