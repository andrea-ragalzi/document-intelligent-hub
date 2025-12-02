/**
 * Component to display tier limits and upgrade options
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
        <div className="flex items-center gap-1.5 text-gray-600 dark:text-gray-400">
          <FileText className="w-3.5 h-3.5" />
          <span>Documents</span>
        </div>
        <span
          className={`font-medium ${
            isClose ? "text-orange-600 dark:text-orange-400" : "text-gray-700 dark:text-gray-300"
          }`}
        >
          {current} / {max}
        </span>
      </div>
      <div className="h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-300 ${
            isClose ? "bg-orange-500" : "bg-blue-500"
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
        <div className="flex items-center gap-1.5 text-gray-600 dark:text-gray-400">
          <MessageSquare className="w-3.5 h-3.5" />
          <span>Queries Today</span>
        </div>
        <span
          className={`font-medium ${
            isClose ? "text-orange-600 dark:text-orange-400" : "text-gray-700 dark:text-gray-300"
          }`}
        >
          {current} / {max === Infinity ? "∞" : max}
        </span>
      </div>
      <div className="h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-300 ${
            isClose ? "bg-orange-500" : "bg-green-500"
          }`}
          style={{ width: `${Math.min(percentage, 100)}%` }}
        />
      </div>
    </div>
  );
}

/**
 * Renders upgrade call-to-action for users approaching limits
 */
function UpgradeCTA({ tier }: { tier: string }) {
  return (
    <div className="mt-4 p-3 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
      <div className="flex items-start gap-2">
        <Crown className="w-4 h-4 text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0" />
        <div className="flex-1 min-w-0">
          <p className="text-xs text-blue-900 dark:text-blue-100 font-medium">
            Upgrade for more capacity
          </p>
          <p className="text-xs text-blue-700 dark:text-blue-300 mt-1">
            Get {tier === "FREE" ? "10x" : "unlimited"} storage with{" "}
            {tier === "FREE" ? "Pro" : "Unlimited"}
          </p>
        </div>
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

  const isDocumentLimitClose = isLimitClose(documentPercentage);
  const isQueryLimitClose = isLimitClose(queryPercentage);
  const showUpgradeCTA = isDocumentLimitClose || isQueryLimitClose;

  return (
    <div className="space-y-4">
      {/* Tier Badge */}
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">Your Plan</h3>
        <TierBadge tier={tier} showUpgrade={!isUnlimited} />
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
          {showUpgradeCTA && <UpgradeCTA tier={tier} />}
        </div>
      )}

      {/* Unlimited Badge */}
      {isUnlimited && (
        <div className="p-3 bg-gradient-to-r from-yellow-50 to-orange-50 dark:from-yellow-900/20 dark:to-orange-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
          <div className="flex items-center gap-2">
            <Crown className="w-4 h-4 text-yellow-600 dark:text-yellow-400" />
            <p className="text-sm text-yellow-900 dark:text-yellow-100 font-medium">
              Unlimited Access
            </p>
          </div>
          <p className="text-xs text-yellow-700 dark:text-yellow-300 mt-1">
            You have full access to all features without limits
          </p>
        </div>
      )}
    </div>
  );
}
