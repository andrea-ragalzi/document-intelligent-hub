"use client";

import { useState } from "react";
import { X } from "lucide-react";

interface GuestDemoBannerProps {
  remaining: number | null;
  limited?: boolean;
  isLoading: boolean;
  hasError?: boolean;
  onViewDocuments: () => void;
  onSignIn: () => void;
  onCreateAccount: () => void;
}

function allowanceLabel(
  remaining: number | null,
  limited: boolean,
  isLoading: boolean,
  hasError: boolean
): string {
  if (isLoading) return "Loading daily allowance…";
  if (hasError) return "Daily allowance unavailable";
  if (!limited) return "Unlimited in development";
  return `${remaining} ${remaining === 1 ? "question" : "questions"} remaining today`;
}

export const GuestDemoBanner: React.FC<GuestDemoBannerProps> = ({
  remaining,
  limited = true,
  isLoading,
  hasError = false,
  onViewDocuments,
  onSignIn,
  onCreateAccount,
}) => {
  const [isCompact, setIsCompact] = useState(false);
  const allowance = allowanceLabel(remaining, limited, isLoading, hasError);

  const actions = (
    <div className="flex flex-wrap items-center gap-1.5 text-xs sm:gap-2 sm:text-sm">
      <button
        type="button"
        className="ui-secondary-action rounded-md px-2.5 py-1.5 sm:px-3 sm:py-2"
        onClick={onViewDocuments}
      >
        View demo documents
      </button>
      <button
        type="button"
        className="ui-secondary-action rounded-md px-2.5 py-1.5 sm:px-3 sm:py-2"
        onClick={onSignIn}
      >
        Sign in
      </button>
      <button
        type="button"
        className="ui-primary-action rounded-md px-2.5 py-1.5 sm:px-3 sm:py-2"
        onClick={onCreateAccount}
      >
        Create account
      </button>
    </div>
  );

  if (isCompact) {
    return (
      <div className="border-b border-accent/25 bg-accent/10 px-3 py-1.5 text-xs text-ink">
        <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-1.5">
          <div className="flex flex-wrap items-center gap-x-2">
            <strong>Demo workspace</strong>
            <span className="font-medium" aria-live="polite">
              {allowance}
            </span>
          </div>
          {actions}
        </div>
      </div>
    );
  }

  return (
    <div className="border-b border-accent/25 bg-accent/10 px-3 py-2 text-xs text-ink sm:px-4 sm:py-3 sm:text-sm">
      <div className="mx-auto flex max-w-5xl flex-col gap-2 sm:flex-row sm:items-center sm:justify-between sm:gap-3">
        <div className="min-w-0">
          <div className="flex items-start justify-between gap-2">
            <p>
              <strong>Demo workspace</strong>. Explore 5 preloaded synthetic InGen documents
              inspired by Jurassic Park.
            </p>
            <button
              type="button"
              aria-label="Minimize demo information"
              className="-mr-1 -mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-md text-muted hover:bg-surface-hover sm:hidden"
              onClick={() => setIsCompact(true)}
            >
              <X size={16} aria-hidden="true" />
            </button>
          </div>
          <p className="mt-0.5 font-medium" aria-live="polite">
            {allowance}
          </p>
        </div>
        {actions}
      </div>
    </div>
  );
};
