export type AuthOperation = "sign-in" | "sign-up" | "sign-out";

const AUTH_ERROR_MESSAGES: Readonly<Record<string, string>> = {
  "auth/account-exists-with-different-credential":
    "An account already exists with this email. Sign in using the original method.",
  "auth/cancelled-popup-request": "Google sign-in was cancelled.",
  "auth/email-already-in-use": "An account already exists with this email.",
  "auth/invalid-credential": "Incorrect email or password.",
  "auth/invalid-email": "Please enter a valid email address.",
  "auth/network-request-failed": "Unable to connect. Check your internet connection and try again.",
  "auth/popup-blocked": "Google sign-in is temporarily unavailable. Please try again.",
  "auth/popup-closed-by-user": "Google sign-in was cancelled.",
  "auth/too-many-requests": "Too many attempts. Please wait and try again.",
  "auth/user-disabled": "This account has been disabled.",
  "auth/user-not-found": "Incorrect email or password.",
  "auth/weak-password": "Please choose a stronger password.",
  "auth/wrong-password": "Incorrect email or password.",
};

const GOOGLE_UNAVAILABLE_CODES = new Set([
  "auth/internal-error",
  "auth/operation-not-allowed",
  "auth/unauthorized-domain",
]);

function getErrorCode(error: unknown): string | null {
  if (typeof error !== "object" || error === null || !("code" in error)) {
    return null;
  }
  return typeof error.code === "string" ? error.code : null;
}

export function getAuthErrorMessage(error: unknown, operation: AuthOperation): string {
  const code = getErrorCode(error);
  if (code && AUTH_ERROR_MESSAGES[code]) {
    return AUTH_ERROR_MESSAGES[code];
  }
  if (code && GOOGLE_UNAVAILABLE_CODES.has(code)) {
    return "Google sign-in is temporarily unavailable. Please try again.";
  }
  if (operation === "sign-out") {
    return "We couldn't sign you out. Please try again.";
  }
  if (operation === "sign-up") {
    return "Something went wrong while creating your account. Please try again.";
  }
  return "Something went wrong while signing you in. Please try again.";
}
