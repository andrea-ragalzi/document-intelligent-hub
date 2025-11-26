"use client";

import { useState } from "react";
import { AlertTriangle, X, Loader } from "lucide-react";

interface DeleteAccountModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => Promise<void>;
  userEmail: string;
}

export const DeleteAccountModal: React.FC<DeleteAccountModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  userEmail,
}) => {
  const [isDeleting, setIsDeleting] = useState(false);
  const [confirmText, setConfirmText] = useState("");

  if (!isOpen) return null;

  const handleConfirm = async () => {
    if (confirmText !== "DELETE") return;

    setIsDeleting(true);
    try {
      await onConfirm();
    } catch (error) {
      console.error("Error deleting account:", error);
    } finally {
      setIsDeleting(false);
    }
  };

  const isConfirmValid = confirmText === "DELETE";

  return (
    <>
      {/* Overlay */}
      <div
        className="fixed inset-0 bg-black/50 dark:bg-indigo-950/80 z-50 transition-opacity duration-300"
        onClick={isDeleting ? undefined : onClose}
        onKeyDown={isDeleting ? undefined : (e) => e.key === 'Escape' && onClose()}
      />

      {/* Modal */}
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 pointer-events-none">
        <div
          className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-md pointer-events-auto transform transition-all duration-300"
          onClick={(e) => e.stopPropagation()}
          onKeyDown={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-red-100 dark:bg-red-900/30">
                <AlertTriangle
                  size={24}
                  className="text-red-600 dark:text-red-400"
                />
              </div>
              <div>
                <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                  Delete Account
                </h2>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  This action cannot be undone
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              disabled={isDeleting}
              className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <X size={24} className="text-gray-500 dark:text-gray-400" />
            </button>
          </div>

          {/* Content */}
          <div className="p-6 space-y-4">
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
              <p className="text-sm text-red-800 dark:text-red-200 font-semibold mb-2">
                Warning: This will permanently delete:
              </p>
              <ul className="text-sm text-red-700 dark:text-red-300 space-y-1 list-disc list-inside">
                <li>Your account ({userEmail})</li>
                <li>All your uploaded documents</li>
                <li>All your conversations</li>
                <li>All your data from our servers</li>
              </ul>
            </div>

            <div>
              <label
                htmlFor="confirmText"
                className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
              >
                Type <span className="font-bold text-red-600">DELETE</span> to
                confirm:
              </label>
              <input
                id="confirmText"
                type="text"
                value={confirmText}
                onChange={(e) => setConfirmText(e.target.value)}
                disabled={isDeleting}
                placeholder="DELETE"
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent bg-white dark:bg-gray-900 text-gray-900 dark:text-white disabled:opacity-50 disabled:cursor-not-allowed"
              />
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center justify-end gap-3 p-6 border-t border-gray-200 dark:border-gray-700">
            <button
              type="button"
              onClick={onClose}
              disabled={isDeleting}
              className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleConfirm}
              disabled={!isConfirmValid || isDeleting}
              className="px-6 py-2 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {isDeleting ? (
                <>
                  <Loader size={16} className="animate-spin" />
                  Deleting...
                </>
              ) : (
                "Delete Account"
              )}
            </button>
          </div>
        </div>
      </div>
    </>
  );
};
