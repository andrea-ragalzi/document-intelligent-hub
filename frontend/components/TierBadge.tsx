/**
 * Badge component to display user tier
 *
 * Shows tier with appropriate styling and allows upgrade action.
 */

import { Crown, Zap, Gift } from "lucide-react";
import { UserTier } from "@/hooks/useUserTier";

interface TierBadgeProps {
  readonly tier: UserTier;
  readonly showUpgrade?: boolean;
  readonly onUpgrade?: () => void;
  readonly className?: string;
}

const TIER_CONFIG = {
  FREE: {
    icon: Gift,
    label: "Free",
    color: "bg-surface border border-line/15 text-muted",
    iconColor: "text-quiet",
  },
  PRO: {
    icon: Zap,
    label: "Pro",
    color: "bg-accent/10 border border-accent/20 text-accent",
    iconColor: "text-accent",
  },
  UNLIMITED: {
    icon: Crown,
    label: "Unlimited",
    color: "bg-warning/10 border border-warning/25 text-warning",
    iconColor: "text-warning",
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
          className="text-xs text-accent hover:text-accent-hover font-medium underline"
        >
          Upgrade
        </button>
      )}
    </div>
  );
}
