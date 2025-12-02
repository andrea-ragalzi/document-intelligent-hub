"use client";

import { useState, useEffect, useCallback } from "react";
import { API_BASE_URL } from "@/lib/constants";

interface UseServerStatusResult {
  isOnline: boolean;
  isChecking: boolean;
  lastChecked: Date | null;
  checkStatus: () => Promise<void>;
}

/**
 * Hook to monitor backend server connectivity
 * Checks server health and provides offline mode support
 */
export const useServerStatus = (): UseServerStatusResult => {
  const [isOnline, setIsOnline] = useState(true);
  const [isChecking, setIsChecking] = useState(false);
  const [lastChecked, setLastChecked] = useState<Date | null>(null);
  const [consecutiveFailures, setConsecutiveFailures] = useState(0);

  const checkStatus = useCallback(async () => {
    setIsChecking(true);
    try {
      // Try to reach the backend health endpoint
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 second timeout

      const response = await fetch(API_BASE_URL.replace("/rag", ""), {
        signal: controller.signal,
        cache: "no-store",
      });

      clearTimeout(timeoutId);

      if (response.ok) {
        setIsOnline(true);
        setConsecutiveFailures(0); // Reset failure count on success
      } else {
        setIsOnline(false);
        setConsecutiveFailures(prev => prev + 1);
      }
    } catch {
      // Only log on first failure to avoid console spam
      if (consecutiveFailures === 0) {
        console.log("⚠️ Server offline - switched to read-only mode");
      }
      setIsOnline(false);
      setConsecutiveFailures(prev => prev + 1);
    } finally {
      setLastChecked(new Date());
      setIsChecking(false);
    }
  }, []);

  // Check on mount
  useEffect(() => {
    checkStatus();
  }, [checkStatus]);

  // Check periodically - longer interval when offline to reduce error spam
  useEffect(() => {
    // 30 seconds when online, 60 seconds when offline
    const interval = setInterval(
      () => {
        checkStatus();
      },
      isOnline ? 30000 : 60000
    );

    return () => clearInterval(interval);
  }, [checkStatus, isOnline]);

  // Check on window focus (user returns to tab)
  useEffect(() => {
    const handleFocus = () => {
      checkStatus();
    };

    window.addEventListener("focus", handleFocus);
    return () => window.removeEventListener("focus", handleFocus);
  }, [checkStatus]);

  return {
    isOnline,
    isChecking,
    lastChecked,
    checkStatus,
  };
};
