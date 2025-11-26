/**
 * useQueryUsage Hook
 *
 * Fetches and manages user's daily query usage from the backend.
 * Returns current usage count, limit, and remaining queries.
 *
 * Uses TanStack Query for caching and automatic refetching.
 */

import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@/contexts/AuthContext";

interface QueryUsageResponse {
  status: string;
  queries_today: number;
  query_limit: number;
  remaining: number;
  tier: string;
}

interface UseQueryUsageResult {
  queriesUsed: number;
  queryLimit: number;
  remaining: number;
  tier: string;
  isLimitReached: boolean;
  isLoading: boolean;
  error: Error | null;
  refetch: () => void;
}

/**
 * Determines if query limit has been reached.
 *
 * Special case: remaining = -1 indicates UNLIMITED tier (never reached).
 *
 * @param remaining - Number of remaining queries (-1 for unlimited, 0 or positive for limited)
 * @returns true if limit is reached, false otherwise
 *
 * @example
 * checkLimitReached(5)    // false - has 5 queries left
 * checkLimitReached(0)    // true  - no queries left
 * checkLimitReached(-1)   // false - UNLIMITED tier
 * checkLimitReached(undefined) // false - no data yet (safe default)
 */
function checkLimitReached(remaining: number | undefined): boolean {
  const UNLIMITED_INDICATOR = -1;

  // No data yet - default to not reached (safe default)
  if (remaining === undefined) {
    return false;
  }

  // UNLIMITED tier - never reached
  if (remaining === UNLIMITED_INDICATOR) {
    return false;
  }

  // Limited tier - check if at or below zero
  return remaining <= 0;
}

/**
 * Custom hook to fetch user's query usage from backend.
 *
 * @returns Query usage data and loading/error states
 */
export function useQueryUsage(): UseQueryUsageResult {
  const { user } = useAuth();

  const { data, isLoading, error, refetch } = useQuery<QueryUsageResponse>({
    queryKey: ["queryUsage", user?.uid],
    queryFn: async () => {
      if (!user) {
        throw new Error("User not authenticated");
      }

      const token = await user.getIdToken();
      const apiUrl =
        process.env.NEXT_PUBLIC_API_BASE_URL?.replace("/rag", "/auth/usage") ||
        "http://localhost:8000/auth/usage";

      const response = await fetch(apiUrl, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        const errorData = await response
          .json()
          .catch(() => ({ detail: "Failed to fetch usage data" }));
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }

      const data = await response.json();
      return data;
    },
    enabled: !!user, // Only run query if user is authenticated
    staleTime: 60000, // Consider data fresh for 1 minute
    refetchInterval: 60000, // Auto-refetch every minute
  });

  return {
    queriesUsed: data?.queries_today ?? 0,
    queryLimit: data?.query_limit ?? 0,
    remaining: data?.remaining ?? 0,
    tier: data?.tier ?? "FREE",
    isLimitReached: checkLimitReached(data?.remaining),
    isLoading,
    error: error ?? null,
    refetch: () => void refetch(),
  };
}
