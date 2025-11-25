/**
 * Hook to get and manage user tier
 *
 * Retrieves tier from Firebase Custom Claims and provides
 * tier-based feature flags.
 */

import { useState, useEffect } from "react";
import { useAuth } from "@/contexts/AuthContext";

export type UserTier = "FREE" | "PRO" | "UNLIMITED";

interface TierLimits {
  maxDocuments: number;
  maxQueriesPerDay: number;
  canUploadMultiple: boolean;
  hasAdvancedFeatures: boolean;
}

const TIER_LIMITS: Record<UserTier, TierLimits> = {
  FREE: {
    maxDocuments: 5,
    maxQueriesPerDay: 20,
    canUploadMultiple: false,
    hasAdvancedFeatures: false,
  },
  PRO: {
    maxDocuments: 50,
    maxQueriesPerDay: 500,
    canUploadMultiple: true,
    hasAdvancedFeatures: true,
  },
  UNLIMITED: {
    maxDocuments: Infinity,
    maxQueriesPerDay: Infinity,
    canUploadMultiple: true,
    hasAdvancedFeatures: true,
  },
};

/**
 * Determines if token should be force-refreshed to get latest custom claims.
 *
 * Force refresh is needed when:
 * 1. First load - ensures we get latest tier after registration
 * 2. Explicit refresh requested - when tier is updated externally
 *
 * @param isFirstLoad - Whether this is the first load of the hook
 * @param refreshTrigger - Counter incremented on explicit refresh requests
 * @returns true if token should be force-refreshed
 */
function shouldForceRefreshToken(
  isFirstLoad: boolean,
  refreshTrigger: number
): boolean {
  return isFirstLoad || refreshTrigger > 0;
}

export function useUserTier() {
  const { user } = useAuth();
  const [tier, setTier] = useState<UserTier>("FREE");
  const [isLoading, setIsLoading] = useState(true);
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [isFirstLoad, setIsFirstLoad] = useState(true);

  useEffect(() => {
    const loadTier = async () => {
      if (!user) {
        setTier("FREE");
        setIsLoading(false);
        return;
      }

      try {
        // Force refresh on first load or explicit refresh to ensure latest tier
        const forceRefresh = shouldForceRefreshToken(
          isFirstLoad,
          refreshTrigger
        );

        console.log(
          `🔄 Loading tier - forceRefresh: ${forceRefresh}, refreshTrigger: ${refreshTrigger}, isFirstLoad: ${isFirstLoad}`
        );

        const idTokenResult = await user.getIdTokenResult(forceRefresh);
        const customTier = idTokenResult.claims.tier as UserTier | undefined;
        console.log(`🎫 Token claims:`, idTokenResult.claims);

        if (customTier && ["FREE", "PRO", "UNLIMITED"].includes(customTier)) {
          setTier(customTier);
          console.log(
            "✅ User tier loaded:",
            customTier,
            forceRefresh ? "(forced refresh)" : "(from cache)"
          );
        } else {
          // No tier set, default to FREE
          setTier("FREE");
          console.log("⚠️ No tier found, defaulting to FREE");
        }

        // Mark first load as complete
        if (isFirstLoad) {
          setIsFirstLoad(false);
        }
      } catch (error) {
        console.error("❌ Error loading tier:", error);
        setTier("FREE");
      } finally {
        setIsLoading(false);
      }
    };

    loadTier();
  }, [user, refreshTrigger]);

  const limits = TIER_LIMITS[tier];

  const canPerformAction = (requiredTier: UserTier): boolean => {
    const tierOrder: UserTier[] = ["FREE", "PRO", "UNLIMITED"];
    const currentIndex = tierOrder.indexOf(tier);
    const requiredIndex = tierOrder.indexOf(requiredTier);
    return currentIndex >= requiredIndex;
  };

  const refreshTier = () => {
    setRefreshTrigger((prev) => prev + 1);
  };

  return {
    tier,
    isLoading,
    limits,
    canPerformAction,
    refreshTier,
    isFree: tier === "FREE",
    isPro: tier === "PRO",
    isUnlimited: tier === "UNLIMITED",
  };
}
