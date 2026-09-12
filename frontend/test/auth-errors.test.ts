import { describe, expect, it } from "vitest";
import { getAuthErrorMessage, type AuthOperation } from "@/lib/authErrors";

describe("Firebase authentication error messages", () => {
  it.each([
    ["auth/invalid-credential", "sign-in", "Incorrect email or password."],
    ["auth/invalid-email", "sign-in", "Please enter a valid email address."],
    ["auth/email-already-in-use", "sign-up", "An account already exists with this email."],
    ["auth/weak-password", "sign-up", "Please choose a stronger password."],
    [
      "auth/network-request-failed",
      "sign-in",
      "Unable to connect. Check your internet connection and try again.",
    ],
    ["auth/popup-closed-by-user", "sign-in", "Google sign-in was cancelled."],
    [
      "auth/unauthorized-domain",
      "sign-in",
      "Google sign-in is temporarily unavailable. Please try again.",
    ],
    [
      "auth/account-exists-with-different-credential",
      "sign-in",
      "An account already exists with this email. Sign in using the original method.",
    ],
  ] satisfies Array<[string, AuthOperation, string]>)(
    "maps %s to a safe user-facing message",
    (code, operation, expected) => {
      expect(getAuthErrorMessage({ code, message: "raw Firebase detail" }, operation)).toBe(
        expected
      );
    }
  );

  it("uses an operation-specific fallback without exposing unknown implementation details", () => {
    expect(getAuthErrorMessage(new Error("Database is closing/hidden"), "sign-in")).toBe(
      "Something went wrong while signing you in. Please try again."
    );
    expect(getAuthErrorMessage(new Error("internal SDK failure"), "sign-out")).toBe(
      "We couldn't sign you out. Please try again."
    );
  });
});
