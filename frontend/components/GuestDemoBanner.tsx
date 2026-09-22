"use client";

import { useEffect, useState } from "react";
import { X } from "lucide-react";

const MOBILE_DEMO_DISMISSED_KEY = "dih_guest_demo_mobile_intro_dismissed";

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
  const [isMobileIntroVisible, setIsMobileIntroVisible] = useState(true);

  useEffect(() => {
    try {
      if (window.sessionStorage.getItem(MOBILE_DEMO_DISMISSED_KEY) === "true") {
        setIsMobileIntroVisible(false);
      }
    } catch {
      // Keep the introduction visible when session storage is unavailable.
    }
  }, []);
  const allowance = allowanceLabel(remaining, limited, isLoading, hasError);

  const dismissMobileIntro = () => {
    setIsMobileIntroVisible(false);
    try {
      window.sessionStorage.setItem(MOBILE_DEMO_DISMISSED_KEY, "true");
    } catch {
      // Keep the dismissal local when session storage is unavailable.
    }
  };

  const desktopActions = (
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

  const mobileActions = (
    <div className="flex flex-wrap items-center justify-center gap-1.5 text-xs">
      <button
        type="button"
        className="ui-secondary-action rounded-md px-2.5 py-1.5"
        onClick={onViewDocuments}
      >
        Documents
      </button>
      <button
        type="button"
        className="ui-secondary-action rounded-md px-2.5 py-1.5"
        onClick={onSignIn}
      >
        Sign in
      </button>
      <button
        type="button"
        className="ui-primary-action rounded-md px-2.5 py-1.5"
        onClick={onCreateAccount}
      >
        Create account
      </button>
    </div>
  );

  const mobileIntro = (
    <div
      data-testid="mobile-demo-banner"
      className="border-b border-accent/25 bg-accent/10 px-3 py-2 text-xs text-ink sm:hidden"
    >
      <div className="mx-auto flex max-w-5xl flex-col gap-2">
        <div className="flex items-start justify-between gap-2">
          <div>
            <p className="font-semibold">You’re exploring the demo</p>
            <p className="mt-0.5">
              5 preloaded InGen documents inspired by <em>Jurassic Park</em>. Ask questions and
              inspect the cited sources.
            </p>
          </div>
          <button
            type="button"
            aria-label="Close demo introduction"
            className="-mr-1 -mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-md text-muted hover:bg-surface-hover"
            onClick={dismissMobileIntro}
          >
            <X size={16} aria-hidden="true" />
          </button>
        </div>
        <div className="flex items-center gap-1.5">
          <button
            type="button"
            className="ui-secondary-action rounded-md px-2.5 py-1.5"
            onClick={onViewDocuments}
          >
            View documents
          </button>
          <button
            type="button"
            className="ui-primary-action rounded-md px-2.5 py-1.5"
            onClick={dismissMobileIntro}
          >
            Got it
          </button>
        </div>
      </div>
    </div>
  );

  const mobileCompact = (
    <div
      data-testid="mobile-demo-banner"
      className="border-b border-accent/25 bg-accent/10 px-3 py-1.5 text-xs text-ink sm:hidden"
    >
      <div className="mx-auto flex flex-col gap-1.5">{mobileActions}</div>
    </div>
  );

  return (
    <>
      {isMobileIntroVisible ? mobileIntro : mobileCompact}
      <div className="hidden border-b border-accent/25 bg-accent/10 px-3 py-2 text-xs text-ink sm:block sm:px-4 sm:py-3 sm:text-sm">
        <div className="mx-auto flex max-w-5xl flex-col gap-2 sm:flex-row sm:items-center sm:justify-between sm:gap-3">
          <div className="min-w-0">
            <p>
              <strong>Demo workspace</strong>. Explore 5 preloaded synthetic InGen documents
              inspired by Jurassic Park.
            </p>
            <p className="mt-0.5 font-medium" aria-live="polite">
              {allowance}
            </p>
          </div>
          {desktopActions}
        </div>
      </div>
    </>
  );
};
