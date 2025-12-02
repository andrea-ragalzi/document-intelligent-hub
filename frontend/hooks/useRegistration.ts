/**
 * Hook for user registration with tier assignment
 *
 * Handles registration flow:
 * 1. Get Firebase ID token
 * 2. Call /auth/register with invitation code
 * 3. Force token refresh to get new custom claims
 * 4. Return assigned tier
 */

import { useState } from "react";
import { useAuth } from "@/contexts/AuthContext";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace("/rag", "") || "http://localhost:8000";

export type UserTier = "FREE" | "PRO" | "UNLIMITED";

export function useRegistration() {
  const { user } = useAuth();
  const [isRegistering, setIsRegistering] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const register = async (invitationCode?: string): Promise<UserTier | null> => {
    if (!user) {
      setError("User not authenticated");
      return null;
    }

    setIsRegistering(true);
    setError(null);

    try {
      // Get Firebase ID token
      const idToken = await user.getIdToken();

      // Call registration endpoint
      const response = await fetch(`${API_BASE_URL}/auth/register`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          id_token: idToken,
          invitation_code: invitationCode || null,
        }),
      });

      // Parse response safely (backend may return non-JSON on errors)
      let data: unknown = null;
      let rawText: string | null = null;
      try {
        data = await response.json();
      } catch {
        // fallback to text if JSON parsing fails
        try {
          rawText = await response.text();
          // keep shape similar to expected JSON
          data = { message: rawText } as unknown;
        } catch {
          data = { message: "Registration failed" } as unknown;
        }
      }

      if (!response.ok) {
        // Backend returns {detail: "error message"} or plain text
        const maybe = data as Record<string, unknown> | null;
        const errorMsg =
          (maybe && (maybe.detail || maybe.message)) || rawText || "Registration failed";
        // Don't throw (avoid uncaught), set local error and return null
        setError(String(errorMsg));
        return null;
      }

      // Force token refresh to get new custom claims
      await user.getIdToken(true);

      const successData = data as { tier: UserTier };
      console.log("✅ Registration successful:", successData.tier);
      return successData.tier;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Registration failed";
      console.error("❌ Registration error:", errorMessage);
      setError(errorMessage);
      return null;
    } finally {
      setIsRegistering(false);
    }
  };

  const clearError = () => {
    setError(null);
  };

  return {
    register,
    isRegistering,
    error,
    clearError,
  };
}
