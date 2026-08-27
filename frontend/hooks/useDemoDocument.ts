"use client";

import { useEffect, useRef, useState } from "react";
import { API_BASE_URL } from "@/lib/constants";
import { useAuth } from "@/contexts/AuthContext";

export type DemoDocumentState = "idle" | "seeding" | "ready" | "failed";

interface DemoDocumentResponse {
  status: "seeded" | "ready";
  filename: string;
  suggested_questions: string[];
}

interface UseDemoDocumentOptions {
  userId: string | null;
  onReady?: () => void | Promise<void>;
}

/** Seed the private starter PDF once per signed-in user without blocking the UI. */
export function useDemoDocument({ userId, onReady }: UseDemoDocumentOptions) {
  const { getIdToken } = useAuth();
  const [state, setState] = useState<DemoDocumentState>("idle");
  const [suggestedQuestions, setSuggestedQuestions] = useState<string[]>([]);
  const attemptedUserId = useRef<string | null>(null);

  useEffect(() => {
    if (!userId) {
      attemptedUserId.current = null;
      setState("idle");
      setSuggestedQuestions([]);
      return;
    }

    if (attemptedUserId.current === userId) return;
    attemptedUserId.current = userId;

    let cancelled = false;
    const seed = async () => {
      setState("seeding");
      try {
        const token = await getIdToken();
        if (!token) throw new Error("No authentication token available");

        const response = await fetch(`${API_BASE_URL}/documents/seed-demo`, {
          method: "POST",
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!response.ok) throw new Error("Demo document seed failed");

        const data: DemoDocumentResponse = await response.json();
        if (cancelled) return;
        setSuggestedQuestions(data.suggested_questions);
        setState("ready");
        await onReady?.();
      } catch (error) {
        if (!cancelled) {
          console.warn("Demo document unavailable; uploads remain available.", error);
          setState("failed");
        }
      }
    };

    void seed();
    return () => {
      cancelled = true;
    };
  }, [getIdToken, onReady, userId]);

  return { state, suggestedQuestions };
}
