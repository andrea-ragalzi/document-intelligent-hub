/**
 * Registration modal for initial account access.
 *
 * Shows on first login if user has no tier assigned.
 * Production requires an invitation code; local development can retain FREE onboarding.
 */

import { Gift, Loader2 } from "lucide-react";
import { useState } from "react";
import { useRegistration } from "@/hooks/useRegistration";
import { requiresInvitationForRegistration } from "@/lib/registration-mode";

interface InvitationCodeModalProps {
  readonly isOpen: boolean;
  readonly onSuccess: (tier: string) => void;
}

export default function InvitationCodeModal({ isOpen, onSuccess }: InvitationCodeModalProps) {
  const { register, isRegistering, error } = useRegistration();
  const [invitationCode, setInvitationCode] = useState("");
  const invitationRequired = requiresInvitationForRegistration();

  if (!isOpen) return null;

  const handleFreeRegistration = async () => {
    try {
      const tier = await register();
      if (tier) {
        onSuccess(tier);
      }
    } catch {
      console.error("Unexpected registration failure.");
    }
  };

  const handleInvitationRegistration = async () => {
    const tier = await register(invitationCode);
    if (tier) {
      onSuccess(tier);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="relative w-full max-w-md bg-white dark:bg-gray-800 rounded-lg shadow-xl">
        {/* Header */}
        <div className="flex items-center gap-3 p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
            <Gift className="w-5 h-5 text-blue-600 dark:text-blue-400" />
          </div>
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
            Welcome to Document Intelligent Hub
          </h2>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4">
          {invitationRequired ? (
            <>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Enter the invitation code you received to activate your account.
              </p>
              <label
                className="block text-sm font-medium text-gray-700 dark:text-gray-300"
                htmlFor="invitation-code"
              >
                Invitation Code
              </label>
              <input
                id="invitation-code"
                value={invitationCode}
                onChange={event => setInvitationCode(event.target.value)}
                autoComplete="off"
                className="w-full rounded-lg border border-gray-300 px-3 py-2 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
              />
            </>
          ) : (
            <>
              <div className="p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
                <p className="text-sm text-yellow-800 dark:text-yellow-200">
                  Your account receives the constrained FREE tier.
                </p>
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                You can upload up to 5 PDFs (10 MB each) and ask up to 20 questions per day.
              </p>
            </>
          )}

          {error && (
            <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
              <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
              <p className="text-xs text-red-500 dark:text-red-400 mt-1">Please try again.</p>
            </div>
          )}

          {/* Actions */}
          <div className="flex flex-col gap-2 pt-2">
            <button
              type="button"
              onClick={invitationRequired ? handleInvitationRegistration : handleFreeRegistration}
              disabled={isRegistering || (invitationRequired && !invitationCode.trim())}
              className="w-full px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-green-400 text-white font-medium rounded-lg transition-colors disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {isRegistering ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Activating...
                </>
              ) : invitationRequired ? (
                "Continue with invitation"
              ) : (
                "Continue with FREE"
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
