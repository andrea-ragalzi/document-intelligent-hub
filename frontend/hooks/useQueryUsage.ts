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
import type { User } from "firebase/auth";

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
 * Builds the API URL for usage endpoint.
 *
 * @returns API URL string
 */
function buildUsageApiUrl(): string {
  return (
    process.env.NEXT_PUBLIC_API_BASE_URL?.replace("/rag", "/auth/usage") ||
    "http://localhost:8000/auth/usage"
  );
}

/**
 * Fetches usage data from backend.
 *
 * @param apiUrl - API endpoint URL
 * @param token - Firebase auth token
 * @returns Response object
 * @throws Error if fetch fails
 */
async function fetchUsageData(apiUrl: string, token: string): Promise<Response> {
  return await fetch(apiUrl, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
  });
}

/**
 * Handles API response errors.
 *
 * @param response - Fetch response
 * @throws Error with error details
 */
async function handleResponseError(response: Response): Promise<never> {
  const errorData = await response.json().catch(() => ({ detail: "Failed to fetch usage data" }));
  throw new Error(errorData.detail || `HTTP ${response.status}`);
}

/**
 * Creates query function for TanStack Query.
 *
 * @param user - Firebase user object
 * @returns Query function
 */
function createQueryFn(user: User | null) {
  return async () => {
    if (!user) {
      throw new Error("User not authenticated");
    }

    const token = await user.getIdToken();
    const apiUrl = buildUsageApiUrl();
    const response = await fetchUsageData(apiUrl, token);

    if (!response.ok) {
      await handleResponseError(response);
    }

    return await response.json();
  };
}

/**
 * Builds result object from query data.
 *
 * @param data - Query response data
 * @param isLoading - Loading state
 * @param error - Error object
 * @param refetch - Refetch function
 * @returns Formatted usage result
 */
function buildUsageResult(
  data: QueryUsageResponse | undefined,
  isLoading: boolean,
  error: Error | null,
  refetch: () => void
): UseQueryUsageResult {
  const queriesUsed = data?.queries_today ?? 0;
  const queryLimit = data?.query_limit ?? 0;
  const remaining = data?.remaining ?? 0;
  const tier = data?.tier ?? "FREE";

  return {
    queriesUsed,
    queryLimit,
    remaining,
    tier,
    isLimitReached: checkLimitReached(remaining),
    isLoading,
    error: error ?? null,
    refetch,
  };
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
    queryFn: createQueryFn(user),
    enabled: !!user,
    staleTime: 60000,
    refetchInterval: 60000,
  });

  return buildUsageResult(data, isLoading, error, refetch);
}
