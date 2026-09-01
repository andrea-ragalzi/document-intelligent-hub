"use client";

import { Suspense, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { EmailVerificationCard } from "@/components/EmailVerificationCard";
import { useAuth } from "@/contexts/AuthContext";
import { useRegistration } from "@/hooks/useRegistration";

function VerifyEmailContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user, loading, logout, refreshEmailVerification, sendVerificationEmail } = useAuth();
  const { register, error: registrationError } = useRegistration();

  useEffect(() => {
    if (!loading && !user) {
      router.replace("/login");
    }
  }, [loading, router, user]);

  const handleCheck = async (): Promise<boolean> => {
    const verified = await refreshEmailVerification();
    if (!verified) {
      return false;
    }

    const tier = await register();
    if (!tier) {
      throw new Error("Registration could not be completed");
    }

    router.replace("/dashboard");
    return true;
  };

  if (loading || !user) {
    return <main className="auth-shell min-h-screen" aria-busy="true" />;
  }

  return (
    <EmailVerificationCard
      email={user.email || "your email address"}
      onResend={sendVerificationEmail}
      onCheck={handleCheck}
      onLogout={logout}
      registrationError={registrationError}
      deliveryFailed={searchParams.get("delivery") === "failed"}
    />
  );
}

export default function VerifyEmailPage() {
  return (
    <Suspense fallback={<main className="auth-shell min-h-screen" aria-busy="true" />}>
      <VerifyEmailContent />
    </Suspense>
  );
}
