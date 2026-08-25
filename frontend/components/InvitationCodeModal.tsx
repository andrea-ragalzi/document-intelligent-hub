/**
 * Registration modal for FREE access or an optional invitation code
 *
 * Shows on first login if user has no tier assigned.
 * Users can continue on FREE without a code; codes remain available for upgrades.
 */

import { useState } from "react";
import { Gift, Loader2 } from "lucide-react";
import { useRegistration } from "@/hooks/useRegistration";
import { useAuth } from "@/contexts/AuthContext";
import RequestCodeModal from "./RequestCodeModal";

interface InvitationCodeModalProps {
  readonly isOpen: boolean;
  readonly onSuccess: (tier: string) => void;
}

export default function InvitationCodeModal({ isOpen, onSuccess }: InvitationCodeModalProps) {
  const [code, setCode] = useState("");
  const [requestModalOpen, setRequestModalOpen] = useState(false);
  const { register, isRegistering, error, clearError } = useRegistration();
  const { user } = useAuth();

  if (!isOpen) return null;

  const handleCodeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newCode = e.target.value.toUpperCase();
    setCode(newCode);
    // Clear error when user starts typing a new code
    if (error) {
      clearError();
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Always require a code - backend will handle unlimited emails
    if (!code.trim()) {
      return; // Button should be disabled anyway
    }

    try {
      const tier = await register(code);
      if (tier) {
        // Call success callback (dashboard will handle closing modal)
        onSuccess(tier);
      }
    } catch (err) {
      // register should not throw, but guard against unexpected errors
      console.error("Unexpected error during registration:", err);
      // setError is handled inside register; no further action required
    }
  };

  const handleFreeRegistration = async () => {
    try {
      const tier = await register();
      if (tier) {
        onSuccess(tier);
      }
    } catch (err) {
      console.error("Unexpected error during FREE registration:", err);
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
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div className="p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
            <p className="text-sm text-yellow-800 dark:text-yellow-200">
              Continue with the constrained FREE tier, or enter an invitation code for elevated
              access.
            </p>
          </div>

          <p className="text-sm text-gray-600 dark:text-gray-400">
            No invitation code is required for FREE access.
          </p>

          <div>
            <label
              htmlFor="invitation-code"
              className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
            >
              Invitation Code
            </label>
            <input
              id="invitation-code"
              type="text"
              value={code}
              onChange={handleCodeChange}
              placeholder="FREE2024"
              disabled={isRegistering}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed"
            />
          </div>

          {error && (
            <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
              <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
              <p className="text-xs text-red-500 dark:text-red-400 mt-1">
                Please try again or use a valid invitation code.
              </p>
            </div>
          )}

          {/* Actions */}
          <div className="flex flex-col gap-2 pt-2">
            <button
              type="button"
              onClick={handleFreeRegistration}
              disabled={isRegistering}
              className="w-full px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-green-400 text-white font-medium rounded-lg transition-colors disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {isRegistering ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Activating...
                </>
              ) : (
                "Continue with FREE"
              )}
            </button>
            <button
              type="submit"
              disabled={isRegistering || !code.trim()}
              className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-medium rounded-lg transition-colors disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {isRegistering ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Activating...
                </>
              ) : (
                "Use Invitation Code"
              )}
            </button>
          </div>

          <p className="text-xs text-gray-500 dark:text-gray-400 text-center">
            Don&apos;t have a code?{" "}
            <button
              type="button"
              onClick={() => setRequestModalOpen(true)}
              disabled={isRegistering}
              className="text-blue-600 dark:text-blue-400 hover:underline font-medium disabled:opacity-50"
            >
              Request one here
            </button>
          </p>
        </form>

        {/* Request Code Modal */}
        <RequestCodeModal
          isOpen={requestModalOpen}
          onClose={() => setRequestModalOpen(false)}
          userEmail={user?.email || undefined}
        />
      </div>
    </div>
  );
}
