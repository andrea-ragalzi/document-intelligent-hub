"use client";

import React, { useEffect } from "react";
import { X } from "lucide-react";

export interface ActionSheetOption {
  icon: React.ReactNode;
  label: string;
  onClick: () => void;
  variant?: "default" | "danger";
}

interface MobileActionSheetProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  options: ActionSheetOption[];
}

export const MobileActionSheet: React.FC<MobileActionSheetProps> = ({
  isOpen,
  onClose,
  title,
  options,
}) => {
  // Close on escape key
  useEffect(() => {
    if (!isOpen) return;

    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };

    document.addEventListener("keydown", handleEscape);
    return () => document.removeEventListener("keydown", handleEscape);
  }, [isOpen, onClose]);

  // Prevent body scroll when open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "unset";
    }

    return () => {
      document.body.style.overflow = "unset";
    };
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop overlay */}
      <div
        className="fixed inset-0 bg-black/40 z-[60] transition-opacity duration-300 ease-in-out animate-fade-in"
        onClick={onClose}
        style={{
          animation: isOpen ? "fadeIn 300ms ease-in-out" : undefined,
        }}
      />

      {/* Action Sheet */}
      <div
        className="fixed bottom-0 left-0 right-0 z-[70] bg-white dark:bg-gray-800 rounded-t-2xl shadow-2xl transform transition-transform duration-300 ease-out"
        style={{
          animation: isOpen ? "slideUp 300ms ease-out" : undefined,
        }}
      >
        {/* Handle bar */}
        <div className="flex justify-center pt-3 pb-2">
          <div className="w-12 h-1 bg-gray-300 dark:bg-gray-600 rounded-full" />
        </div>

        {/* Header with title and close button */}
        {title && (
          <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              {title}
            </h3>
            <button
              onClick={onClose}
              className="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700 transition"
            >
              <X size={20} className="text-gray-500 dark:text-gray-400" />
            </button>
          </div>
        )}

        {/* Options list */}
        <div className="py-2">
          {options.map((option) => (
            <button
              key={option.label}
              onClick={() => {
                option.onClick();
                onClose();
              }}
              className={`w-full flex items-center gap-4 px-6 py-4 text-left transition-colors ${
                option.variant === "danger"
                  ? "hover:bg-red-50 dark:hover:bg-red-900/20 text-red-600 dark:text-red-400"
                  : "hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-900 dark:text-gray-100"
              }`}
            >
              <div
                className={`flex-shrink-0 ${
                  option.variant === "danger"
                    ? "text-red-600 dark:text-red-400"
                    : "text-gray-600 dark:text-gray-400"
                }`}
              >
                {option.icon}
              </div>
              <span className="text-base font-medium">{option.label}</span>
            </button>
          ))}
        </div>

        {/* Safe area padding for iOS */}
        <div className="h-safe-area-inset-bottom pb-4" />
      </div>

      <style jsx>{`
        @keyframes fadeIn {
          from {
            opacity: 0;
          }
          to {
            opacity: 1;
          }
        }

        @keyframes slideUp {
          from {
            transform: translateY(100%);
          }
          to {
            transform: translateY(0);
          }
        }

        .h-safe-area-inset-bottom {
          height: env(safe-area-inset-bottom, 0px);
        }
      `}</style>
    </>
  );
};
