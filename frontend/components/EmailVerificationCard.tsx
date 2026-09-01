"use client";

import { useState } from "react";

interface EmailVerificationCardProps {
  readonly email: string;
  readonly onResend: () => Promise<void>;
  readonly onCheck: () => Promise<boolean>;
  readonly onLogout?: () => Promise<void>;
  readonly registrationError?: string | null;
  readonly deliveryFailed?: boolean;
}

export function EmailVerificationCard({
  email,
  onResend,
  onCheck,
  onLogout,
  registrationError = null,
  deliveryFailed = false,
}: EmailVerificationCardProps) {
  const [isResending, setIsResending] = useState(false);
  const [isChecking, setIsChecking] = useState(false);
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleResend = async () => {
    setError(null);
    setStatus(null);
    setIsResending(true);
    try {
      await onResend();
      setStatus("A new verification email has been sent.");
    } catch {
      setError("We could not send a verification email. Please try again.");
    } finally {
      setIsResending(false);
    }
  };

  const handleCheck = async () => {
    setError(null);
    setStatus(null);
    setIsChecking(true);
    try {
      const verified = await onCheck();
      if (!verified) {
        setStatus("Your email is not verified yet. Open the link in your inbox and try again.");
      }
    } catch {
      setError("We could not refresh your verification status. Please try again.");
    } finally {
      setIsChecking(false);
    }
  };

  return (
    <main className="auth-shell flex min-h-screen items-center justify-center px-4 py-12 sm:px-6 lg:px-8">
      <section
        className="ui-panel w-full max-w-md rounded-xl p-6"
        aria-labelledby="verify-email-title"
      >
        <h1 id="verify-email-title" className="text-center text-2xl font-semibold text-ink">
          Verify your email
        </h1>
        <p className="mt-4 text-center text-sm text-muted">
          We sent a verification link to <span className="font-medium text-ink">{email}</span>.
        </p>
        <p className="mt-2 text-center text-sm text-muted">
          Verify your address, then return here to activate your FREE account.
        </p>

        {deliveryFailed && (
          <p
            className="mt-4 rounded-md border border-danger/30 bg-danger/10 p-3 text-sm text-danger"
            role="alert"
          >
            Your account was created, but the verification email could not be sent. Please resend
            it.
          </p>
        )}

        {status && (
          <p
            className="mt-4 rounded-md border border-accent/30 bg-accent/10 p-3 text-sm text-ink"
            role="status"
          >
            {status}
          </p>
        )}
        {(error || registrationError) && (
          <p
            className="mt-4 rounded-md border border-danger/30 bg-danger/10 p-3 text-sm text-danger"
            role="alert"
          >
            {error || registrationError}
          </p>
        )}

        <div className="mt-6 flex flex-col gap-3">
          <button
            type="button"
            onClick={() => void handleCheck()}
            disabled={isChecking || isResending}
            className="ui-primary-action w-full rounded-md px-4 py-2 font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-50"
          >
            {isChecking ? "Checking…" : "I’ve verified"}
          </button>
          <button
            type="button"
            onClick={() => void handleResend()}
            disabled={isChecking || isResending}
            className="ui-secondary-action w-full rounded-md px-4 py-2 font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-50"
          >
            {isResending ? "Sending…" : "Resend verification email"}
          </button>
          {onLogout && (
            <button
              type="button"
              onClick={() => void onLogout()}
              className="text-sm font-medium text-muted transition-colors hover:text-ink"
            >
              Use a different account
            </button>
          )}
        </div>
      </section>
    </main>
  );
}
