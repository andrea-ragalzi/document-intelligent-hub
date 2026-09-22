import { describe, expect, it, vi } from "vitest";
import { rethrowAccountDeletionFailure } from "@/lib/accountDeletionErrors";

describe("account deletion failures", () => {
  it.each([
    ["auth/wrong-password", "The password is incorrect. Please try again."],
    ["auth/invalid-credential", "The password is incorrect. Please try again."],
    ["auth/popup-closed-by-user", "Sign-in was cancelled. Your account has not been deleted."],
    ["auth/too-many-requests", "Unable to verify your identity. Please try again."],
  ])("shows %s inline without logging", (code, expectedMessage) => {
    const consoleError = vi.spyOn(console, "error").mockImplementation(() => undefined);

    expect(() => rethrowAccountDeletionFailure({ code })).toThrow(expectedMessage);
    expect(consoleError).not.toHaveBeenCalled();

    consoleError.mockRestore();
  });

  it("logs an unexpected failure once without logging the error payload", () => {
    const consoleError = vi.spyOn(console, "error").mockImplementation(() => undefined);
    const unexpectedFailure = new Error("backend response containing sensitive details");

    expect(() => rethrowAccountDeletionFailure(unexpectedFailure)).toThrow(unexpectedFailure);
    expect(consoleError).toHaveBeenCalledTimes(1);
    expect(consoleError).toHaveBeenCalledWith("Account deletion failed.");

    consoleError.mockRestore();
  });
});
