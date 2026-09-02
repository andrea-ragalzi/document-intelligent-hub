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
  if (trimmed.length > 1500) {
    return { isValid: false, error: "Please keep the description under 1,500 characters" };
  }
  return { isValid: true };
}

/**
 * Creates FormData for bug report submission
 */
export function createBugReportFormData(
  description: string,
  conversationId?: string | null,
  attachedFile?: File | null
): FormData {
  const formData = new FormData();
  formData.append("description", description.trim());

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
export async function submitBugReport(formData: FormData, token: string): Promise<void> {
  const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/report-bug/`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: formData,
  });

  if (!response.ok) {
    if (response.status === 413) {
      throw new Error("Screenshot too large. Maximum size is 5MB. Please try a smaller image.");
    }

    const errorData = await response.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(errorData.detail || "Failed to submit bug report");
  }
}
