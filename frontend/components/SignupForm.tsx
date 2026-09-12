"use client";

import { useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { useRouter } from "next/navigation";
import {
  AuthProviderDivider,
  AuthErrorMessage,
  AuthTextField,
  AuthSubmitButton,
  GoogleAuthButton,
} from "@/components/AuthFormControls";
import { useAuthRequest } from "@/hooks/useAuthRequest";

export default function SignupForm() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const { signUp, signInWithGoogle } = useAuth();
  const router = useRouter();
  const { error, isLoading, pendingAction, run, setError } = useAuthRequest();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    if (password.length < 6) {
      setError("Password must be at least 6 characters");
      return;
    }

    const succeeded = await run(
      "email",
      async () => {
        const result = await signUp(email, password);
        router.replace(
          result.verificationEmailSent ? "/verify-email" : "/verify-email?delivery=failed"
        );
      },
      "Something went wrong while creating your account. Please try again."
    );
    if (!succeeded) {
      return;
    }
  };

  const handleGoogleSignIn = async () => {
    const succeeded = await run(
      "google",
      signInWithGoogle,
      "Google sign-in is temporarily unavailable. Please try again."
    );
    if (succeeded) {
      router.push("/");
    }
  };

  return (
    <div className="ui-panel max-w-md mx-auto mt-8 p-6 rounded-xl">
      <h2 className="text-2xl font-semibold mb-6 text-center text-ink">Create Account</h2>

      {error && <AuthErrorMessage message={error} />}

      <form onSubmit={handleSubmit} className="space-y-4">
        <AuthTextField
          id="email"
          label="Email"
          type="email"
          value={email}
          onChange={event => setEmail(event.target.value)}
          disabled={isLoading}
        />
        <AuthTextField
          id="password"
          label="Password"
          type="password"
          value={password}
          onChange={event => setPassword(event.target.value)}
          disabled={isLoading}
          minLength={6}
        />
        <AuthTextField
          id="confirmPassword"
          label="Confirm Password"
          type="password"
          value={confirmPassword}
          onChange={event => setConfirmPassword(event.target.value)}
          disabled={isLoading}
          minLength={6}
        />

        <AuthSubmitButton
          action="email"
          label="Sign Up"
          pendingLabel="Creating account..."
          pendingAction={pendingAction}
        />
      </form>

      <div className="mt-4">
        <AuthProviderDivider />
        <GoogleAuthButton onClick={handleGoogleSignIn} disabled={isLoading}>
          {pendingAction === "google" ? "Signing up with Google..." : "Sign up with Google"}
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
