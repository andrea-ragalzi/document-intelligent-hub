"use client";

import { useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { useRouter } from "next/navigation";
import {
  AuthProviderDivider,
  AuthTextField,
  GoogleAuthButton,
} from "@/components/AuthFormControls";

export default function SignupForm() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { signUp, signInWithGoogle } = useAuth();
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    if (password.length < 6) {
      setError("Password must be at least 6 characters");
      return;
    }

    setLoading(true);

    try {
      await signUp(email, password);
      router.push("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create account");
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSignIn = async () => {
    setError("");
    setLoading(true);

    try {
      await signInWithGoogle();
      router.push("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to sign in with Google");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="ui-panel max-w-md mx-auto mt-8 p-6 rounded-xl">
      <h2 className="text-2xl font-semibold mb-6 text-center text-ink">Create Account</h2>

      {error && (
        <div className="mb-4 p-3 bg-red-100 dark:bg-red-900/30 border border-red-400 text-red-700 dark:text-red-400 rounded">
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
          minLength={6}
        />
        <AuthTextField
          id="confirmPassword"
          label="Confirm Password"
          type="password"
          value={confirmPassword}
          onChange={event => setConfirmPassword(event.target.value)}
          disabled={loading}
          minLength={6}
        />

        <button
          type="submit"
          disabled={loading}
          className="ui-primary-action w-full font-medium py-2 px-4 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? "Creating account..." : "Sign Up"}
        </button>
      </form>

      <div className="mt-4">
        <AuthProviderDivider />
        <GoogleAuthButton onClick={handleGoogleSignIn} disabled={loading}>
          Sign up with Google
        </GoogleAuthButton>
      </div>

      <p className="mt-4 text-center text-sm text-muted">
        Already have an account?{" "}
        <a href="/login" className="text-accent hover:text-accent-hover font-medium">
          Sign in
        </a>
      </p>
    </div>
  );
}
