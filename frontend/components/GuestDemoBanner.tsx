interface GuestDemoBannerProps {
  remaining: number | null;
  limited?: boolean;
  isLoading: boolean;
  hasError?: boolean;
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
  onSignIn,
  onCreateAccount,
}) => (
  <div className="border-b border-accent/25 bg-accent/10 px-4 py-3 text-sm text-ink">
    <div className="mx-auto flex max-w-5xl flex-col items-start justify-between gap-3 sm:flex-row sm:items-center">
      <div>
        <p>
          <strong>Demo workspace</strong>. Five preloaded synthetic InGen documents are read-only.
          They are fan-made demo artifacts, not official franchise material.
        </p>
        <p className="mt-1 font-medium" aria-live="polite">
          {allowanceLabel(remaining, limited, isLoading, hasError)}
        </p>
        <p className="mt-1 text-muted">Sign in or create an account to upload private documents.</p>
      </div>
      <div className="flex shrink-0 gap-2">
        <button className="ui-secondary-action rounded-lg px-3 py-2" onClick={onSignIn}>
          Sign in
        </button>
        <button className="ui-primary-action rounded-lg px-3 py-2" onClick={onCreateAccount}>
          Create account
        </button>
      </div>
    </div>
  </div>
);
