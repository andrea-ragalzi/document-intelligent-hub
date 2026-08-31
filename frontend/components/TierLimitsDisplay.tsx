/**
 * Component to display tier limits.
 */

import { FileText, MessageSquare, Crown } from "lucide-react";
import { useUserTier } from "@/hooks/useUserTier";
import TierBadge from "./TierBadge";

interface TierLimitsDisplayProps {
  readonly currentDocuments?: number;
  readonly currentQueries?: number;
}

/**
 * Determines if a limit is close to being reached (>80%)
 */
function isLimitClose(percentage: number): boolean {
  return percentage > 80;
}

/**
 * Renders the document limit progress bar
 */
function DocumentLimitBar({
  current,
  max,
  percentage,
}: {
  current: number;
  max: number;
  percentage: number;
}) {
  const isClose = isLimitClose(percentage);

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-xs">
        <div className="flex items-center gap-1.5 text-muted">
          <FileText className="w-3.5 h-3.5" />
          <span>Documents</span>
        </div>
        <span className={`font-medium ${isClose ? "text-warning" : "text-muted"}`}>
          {current} / {max}
        </span>
      </div>
      <div className="h-1.5 bg-line/15 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-300 ${
            isClose ? "bg-warning" : "bg-accent"
          }`}
          style={{ width: `${Math.min(percentage, 100)}%` }}
        />
      </div>
    </div>
  );
}

/**
 * Renders the queries limit progress bar
 */
function QueryLimitBar({
  current,
  max,
  percentage,
}: {
  current: number;
  max: number;
  percentage: number;
}) {
  const isClose = isLimitClose(percentage);

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-xs">
        <div className="flex items-center gap-1.5 text-muted">
          <MessageSquare className="w-3.5 h-3.5" />
          <span>Queries Today</span>
        </div>
        <span className={`font-medium ${isClose ? "text-warning" : "text-muted"}`}>
          {current} / {max === Infinity ? "∞" : max}
        </span>
      </div>
      <div className="h-1.5 bg-line/15 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-300 ${
            isClose ? "bg-warning" : "bg-success"
          }`}
          style={{ width: `${Math.min(percentage, 100)}%` }}
        />
      </div>
    </div>
  );
}

export default function TierLimitsDisplay({
  currentDocuments = 0,
  currentQueries = 0,
}: TierLimitsDisplayProps) {
  const { tier, limits, isUnlimited } = useUserTier();

  const documentPercentage = isUnlimited ? 0 : (currentDocuments / limits.maxDocuments) * 100;
  const queryPercentage = isUnlimited ? 0 : (currentQueries / limits.maxQueriesPerDay) * 100;

  return (
    <div className="space-y-4">
      {/* Tier Badge */}
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-muted">Your Plan</h3>
        <TierBadge tier={tier} />
      </div>

      {/* Limits */}
      {!isUnlimited && (
        <div className="space-y-3">
          <DocumentLimitBar
            current={currentDocuments}
            max={limits.maxDocuments}
            percentage={documentPercentage}
          />
          <QueryLimitBar
            current={currentQueries}
            max={limits.maxQueriesPerDay}
            percentage={queryPercentage}
          />
        </div>
      )}

      {/* Unlimited Badge */}
      {isUnlimited && (
        <div className="p-3 bg-warning/10 border border-warning/25 rounded-lg">
          <div className="flex items-center gap-2">
            <Crown className="w-4 h-4 text-warning" />
            <p className="text-sm text-ink font-medium">Unlimited Access</p>
          </div>
          <p className="text-xs text-muted mt-1">
            You have full access to all features without limits
          </p>
        </div>
      )}
    </div>
  );
}
