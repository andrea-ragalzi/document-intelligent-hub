/**
 * Badge component to display user tier
 *
 * Shows tier with appropriate styling and allows upgrade action.
 */

import { Crown, Zap, Gift } from "lucide-react";
import { UserTier } from "@/hooks/useUserTier";

interface TierBadgeProps {
  tier: UserTier;
  showUpgrade?: boolean;
  onUpgrade?: () => void;
  className?: string;
}

const TIER_CONFIG = {
  FREE: {
    icon: Gift,
    label: "Free",
    color: "bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300",
    iconColor: "text-gray-500 dark:text-gray-400",
  },
  PRO: {
    icon: Zap,
    label: "Pro",
    color: "bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300",
    iconColor: "text-blue-600 dark:text-blue-400",
  },
  UNLIMITED: {
    icon: Crown,
    label: "Unlimited",
    color:
      "bg-gradient-to-r from-yellow-100 to-orange-100 dark:from-yellow-900/30 dark:to-orange-900/30 text-yellow-800 dark:text-yellow-300",
    iconColor: "text-yellow-600 dark:text-yellow-400",
  },
};

export default function TierBadge({
  tier,
  showUpgrade = false,
  onUpgrade,
  className = "",
}: TierBadgeProps) {
  const config = TIER_CONFIG[tier];
  const Icon = config.icon;

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <div
        className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium ${config.color}`}
      >
        <Icon className={`w-4 h-4 ${config.iconColor}`} />
        {config.label}
      </div>

      {showUpgrade && tier !== "UNLIMITED" && onUpgrade && (
        <button
          onClick={onUpgrade}
          className="text-xs text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 font-medium underline"
        >
          Upgrade
        </button>
      )}
    </div>
  );
}
