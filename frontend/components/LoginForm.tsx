"use client";

import { useRef, useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { useRouter } from "next/navigation";
import {
  AuthProviderDivider,
  AuthTextField,
  GoogleAuthButton,
} from "@/components/AuthFormControls";

export default function LoginForm() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [pendingAction, setPendingAction] = useState<"email" | "google" | null>(null);
  const requestInFlight = useRef(false);
  const { signIn, signInWithGoogle } = useAuth();
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (requestInFlight.current) return;
    requestInFlight.current = true;
    setError("");
    setPendingAction("email");

    try {
      await signIn(email, password);
      router.push("/");
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Something went wrong while signing you in. Please try again."
      );
    } finally {
      requestInFlight.current = false;
      setPendingAction(null);
    }
  };

  const handleGoogleSignIn = async () => {
    if (requestInFlight.current) return;
    requestInFlight.current = true;
    setError("");
    setPendingAction("google");

    try {
      await signInWithGoogle();
      router.push("/");
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Google sign-in is temporarily unavailable. Please try again."
      );
    } finally {
      requestInFlight.current = false;
      setPendingAction(null);
    }
  };

  const loading = pendingAction !== null;

  return (
    <div className="ui-panel max-w-md mx-auto mt-8 p-6 rounded-xl">
      <h2 className="text-2xl font-semibold mb-6 text-center text-ink">Sign In</h2>

      {error && (
        <div
          className="mb-4 p-3 bg-red-100 dark:bg-red-900/30 border border-red-400 text-red-700 dark:text-red-400 rounded"
          role="alert"
        >
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <AuthTextField
          id="email"
          label="Email"
          type="email"
          value={email}
          onChange={event => setEmail(event.target.value)}
          disabled={loading}
        />
        <AuthTextField
          id="password"
          label="Password"
          type="password"
          value={password}
          onChange={event => setPassword(event.target.value)}
          disabled={loading}
        />

        <button
          type="submit"
          disabled={loading}
          className="ui-primary-action w-full font-medium py-2 px-4 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {pendingAction === "email" ? "Signing in..." : "Sign In"}
        </button>
      </form>

      <div className="mt-4">
        <AuthProviderDivider />
        <GoogleAuthButton onClick={handleGoogleSignIn} disabled={loading}>
          {pendingAction === "google" ? "Signing in with Google..." : "Sign in with Google"}
        </GoogleAuthButton>
      </div>

      <p className="mt-4 text-center text-sm text-muted">
        Don&apos;t have an account?{" "}
        <a href="/signup" className="text-accent hover:text-accent-hover font-medium">
          Sign up
        </a>
      </p>
    </div>
  );
}
