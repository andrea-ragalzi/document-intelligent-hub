/**
 * Helper functions for chat form submission
 */

import { FormEvent } from "react";

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
  return Boolean(query.trim() && !isQuerying && userId && !isChatDisabled);
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
  resetTextareaHeight: () => void
) {
  return (e: FormEvent) => {
    e.preventDefault();

    if (!canSubmitQuery(query, isQuerying, userId, isChatDisabled)) {
      return;
    }

    onQuerySubmit(e);
    resetTextareaHeight();
  };
}
