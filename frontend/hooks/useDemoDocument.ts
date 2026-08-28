"use client";

import { useEffect, useRef, useState } from "react";
import { API_BASE_URL } from "@/lib/constants";
import { useAuth } from "@/contexts/AuthContext";

export type DemoDocumentState = "idle" | "seeding" | "ready" | "failed";

// A transient gateway error must not leave a newly signed-in user stuck in the
// failed state. Keep this deliberately small: the endpoint is idempotent and
// this is the only automatic retry performed for a dashboard session.
const DEMO_SEED_RETRY_DELAY_MS = 750;
const DEMO_SEED_MAX_ATTEMPTS = 2;

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
    const refreshDocumentState = async () => {
      // Refresh both the list and the chat availability after either outcome:
      // a proxy can report a transient error after the backend has indexed it.
      await onReady?.();
    };

    const seed = async () => {
      setState("seeding");
      for (let attempt = 1; attempt <= DEMO_SEED_MAX_ATTEMPTS; attempt += 1) {
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
          await refreshDocumentState();
          return;
        } catch (error) {
          if (cancelled) return;
          if (attempt < DEMO_SEED_MAX_ATTEMPTS) {
            await new Promise(resolve => setTimeout(resolve, DEMO_SEED_RETRY_DELAY_MS));
            continue;
          }

          console.warn("Demo document unavailable; uploads remain available.", error);
          setState("failed");
          await refreshDocumentState();
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
