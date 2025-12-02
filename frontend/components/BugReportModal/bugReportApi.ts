/**
 * Bug report submission logic
 */

/**
 * Validates description before submission
 */
export function validateDescription(description: string): {
  isValid: boolean;
  error?: string;
} {
  const trimmed = description.trim();
  if (!trimmed || trimmed.length < 10) {
    return {
      isValid: false,
      error: "Please provide at least 10 characters description",
    };
  }
  return { isValid: true };
}

/**
 * Creates FormData for bug report submission
 */
export function createBugReportFormData(
  userId: string | null | undefined,
  description: string,
  conversationId?: string | null,
  attachedFile?: File | null
): FormData {
  const formData = new FormData();
  formData.append("user_id", userId || "anonymous");
  formData.append("description", description.trim());
  formData.append("timestamp", new Date().toISOString());
  formData.append("user_agent", navigator.userAgent);

  if (conversationId) {
    formData.append("conversation_id", conversationId);
  }

  if (attachedFile) {
    formData.append("attachment", attachedFile);
  }

  return formData;
}

/**
 * Submits bug report to API
 */
export async function submitBugReport(formData: FormData): Promise<void> {
  const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/report-bug`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    if (response.status === 413) {
      throw new Error(
        "File too large. Maximum size is 10MB. Please try a smaller file or compress it."
      );
    }

    const errorData = await response.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(errorData.detail || "Failed to submit bug report");
  }
}
