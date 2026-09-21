const EXPECTED_ACCOUNT_DELETION_ERRORS: Readonly<Record<string, string>> = {
  "auth/invalid-credential": "The password is incorrect. Please try again.",
  "auth/popup-closed-by-user": "Sign-in was cancelled. Your account has not been deleted.",
  "auth/wrong-password": "The password is incorrect. Please try again.",
};

function getErrorCode(error: unknown): string | null {
  if (typeof error !== "object" || error === null || !("code" in error)) {
    return null;
  }
  return typeof error.code === "string" ? error.code : null;
}

export function rethrowAccountDeletionFailure(error: unknown): never {
  const errorCode = getErrorCode(error);
  const userMessage = errorCode ? EXPECTED_ACCOUNT_DELETION_ERRORS[errorCode] : undefined;

  if (userMessage) {
    throw new Error(userMessage);
  }

  if (errorCode?.startsWith("auth/")) {
    throw new Error("Unable to verify your identity. Please try again.");
  }

  // Keep the log payload-free: Firebase errors can contain authentication details.
  console.error("Account deletion failed.");
  throw error;
}
