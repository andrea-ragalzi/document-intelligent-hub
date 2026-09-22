import { useRef, useState } from "react";

export type AuthAction = "email" | "google" | "demo";
type AuthRequest = () => Promise<void>;

/** Shares loading, duplicate-submit protection, and safe error state across auth forms. */
export function useAuthRequest() {
  const [pendingAction, setPendingAction] = useState<AuthAction | null>(null);
  const [error, setError] = useState("");
  const requestInFlight = useRef(false);

  const run = async (
    action: AuthAction,
    request: AuthRequest,
    fallbackMessage: string
  ): Promise<boolean> => {
    if (requestInFlight.current) return false;
    requestInFlight.current = true;
    setError("");
    setPendingAction(action);

    try {
      await request();
      return true;
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : fallbackMessage);
      return false;
    } finally {
      requestInFlight.current = false;
      setPendingAction(null);
    }
  };

  const runDemo = async (request: AuthRequest, onSuccess: () => void): Promise<void> => {
    const succeeded = await run(
      "demo",
      request,
      "The demo is temporarily unavailable. Please try again."
    );
    if (succeeded) onSuccess();
  };

  return { error, isLoading: pendingAction !== null, pendingAction, run, runDemo, setError };
}
