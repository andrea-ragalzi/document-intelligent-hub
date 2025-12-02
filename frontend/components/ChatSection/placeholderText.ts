/**
 * Placeholder text helper for chat input
 */

export function getPlaceholderText(
  isServerOnline: boolean,
  isLimitReached: boolean,
  isChatDisabled: boolean
): string {
  if (isServerOnline === false) {
    return "Server offline - Read only mode...";
  }
  if (isLimitReached) {
    return "Daily query limit reached. Upgrade your plan or try again tomorrow...";
  }
  if (isChatDisabled) {
    return "Upload a document first...";
  }
  return "Ask me anything...";
}
