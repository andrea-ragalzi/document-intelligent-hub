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

export default function LoginForm() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const { signIn, signInWithGoogle } = useAuth();
  const router = useRouter();
  const { error, isLoading, pendingAction, run } = useAuthRequest();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const succeeded = await run(
      "email",
      async () => {
        await signIn(email, password);
      },
      "Something went wrong while signing you in. Please try again."
    );
    if (succeeded) {
      router.push("/");
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
      <h2 className="text-2xl font-semibold mb-6 text-center text-ink">Sign In</h2>

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
        />

        <AuthSubmitButton
          action="email"
          label="Sign In"
          pendingLabel="Signing in..."
          pendingAction={pendingAction}
        />
      </form>

      <div className="mt-4">
        <AuthProviderDivider />
        <GoogleAuthButton onClick={handleGoogleSignIn} disabled={isLoading}>
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
