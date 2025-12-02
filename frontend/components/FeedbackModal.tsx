import { Star, X } from "lucide-react";
import { useState } from "react";

interface FeedbackModalProps {
  isOpen: boolean;
  onClose: () => void;
  conversationId?: string | null;
  userId?: string | null;
}

export const FeedbackModal: React.FC<FeedbackModalProps> = ({
  isOpen,
  onClose,
  conversationId,
  userId,
}) => {
  const [rating, setRating] = useState<number>(0);
  const [hoverRating, setHoverRating] = useState<number>(0);
  const [message, setMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitStatus, setSubmitStatus] = useState<"idle" | "success" | "error">("idle");
  const [errorMessage, setErrorMessage] = useState("");

  if (!isOpen) return null;

  const handleStarClick = (value: number) => {
    // Toggle: if clicking the same value, reset to 0
    if (rating === value) {
      setRating(0);
    } else {
      setRating(value);
    }
  };

  const handleStarHover = (value: number) => {
    setHoverRating(value);
  };

  const handleMouseLeave = () => {
    setHoverRating(0);
  };

  const displayRating = hoverRating || rating;

  const renderStar = (position: number) => {
    const isFilled = displayRating >= position;

    return (
      <button
        key={position}
        type="button"
        onClick={() => handleStarClick(position)}
        onMouseEnter={() => handleStarHover(position)}
        onMouseLeave={handleMouseLeave}
        className="inline-block cursor-pointer select-none focus:outline-none"
      >
        <Star
          size={48}
          className={`transition-all ${
            isFilled
              ? "fill-yellow-400 text-yellow-400"
              : "fill-none text-gray-300 dark:text-gray-600"
          }`}
        />
      </button>
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (rating === 0) {
      setErrorMessage("Please select a rating");
      setSubmitStatus("error");
      return;
    }

    setIsSubmitting(true);
    setSubmitStatus("idle");
    setErrorMessage("");

    try {
      const payload = {
        user_id: userId || "anonymous",
        conversation_id: conversationId || null,
        rating: rating,
        message: message.trim() || null,
        timestamp: new Date().toISOString(),
        user_agent: navigator.userAgent,
      };

      console.log("Sending feedback:", payload);

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/feedback`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: "Unknown error" }));
        console.error("Feedback submission failed:", response.status, errorData);
        throw new Error(errorData.detail || "Failed to submit feedback");
      }

      setSubmitStatus("success");
      setRating(0);
      setMessage("");

      // Close modal after 2 seconds
      setTimeout(() => {
        onClose();
        setSubmitStatus("idle");
      }, 2000);
    } catch (error) {
      console.error("Error submitting feedback:", error);
      setErrorMessage(error instanceof Error ? error.message : "Failed to submit feedback");
      setSubmitStatus("error");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    if (!isSubmitting) {
      setRating(0);
      setMessage("");
      setSubmitStatus("idle");
      setErrorMessage("");
      setHoverRating(0);
      onClose();
    }
  };

  const getRatingLabel = (value: number): string => {
    if (value === 0) return "Select your rating";
    if (value === 1) return "Poor";
    if (value === 2) return "Fair";
    if (value === 3) return "Good";
    if (value === 4) return "Very Good";
    return "Excellent";
  };

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 dark:bg-indigo-950/80 z-50 transition-opacity"
        onClick={handleClose}
      />

      {/* Modal */}
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div
          className="bg-white dark:bg-indigo-900 rounded-xl shadow-2xl w-full max-w-lg border-2 border-indigo-200 dark:border-indigo-700"
          onClick={e => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b-2 border-indigo-200 dark:border-indigo-700">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-yellow-100 dark:bg-yellow-900/30 rounded-lg">
                <Star size={24} className="text-yellow-600 dark:text-yellow-400 fill-current" />
              </div>
              <h2 className="text-xl font-semibold text-indigo-900 dark:text-indigo-50">
                Rate Your Experience
              </h2>
            </div>
            <button
              onClick={handleClose}
              disabled={isSubmitting}
              className="p-2 hover:bg-indigo-100 dark:hover:bg-indigo-800 rounded-lg transition-colors disabled:opacity-50"
            >
              <X size={24} className="text-indigo-700 dark:text-indigo-200" />
            </button>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="p-6 space-y-6">
            {/* Info Banner */}
            <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
              <p className="text-sm text-blue-900 dark:text-blue-200">
                <strong>ℹ️ Your feedback matters:</strong> Help us improve by rating your experience
                and sharing your thoughts.
              </p>
            </div>

            {/* Conversation ID Display (if available) */}
            {conversationId && (
              <div className="p-3 bg-indigo-50 dark:bg-indigo-950 rounded-lg border border-indigo-200 dark:border-indigo-800">
                <p className="text-sm text-indigo-700 dark:text-indigo-300">
                  <span className="font-semibold">📍 Current Conversation:</span>{" "}
                  <code className="text-xs break-all">{conversationId}</code>
                </p>
              </div>
            )}

            {/* Star Rating */}
            <div className="text-center">
              <label className="block text-sm font-medium text-indigo-900 dark:text-indigo-50 mb-3">
                How would you rate your experience? *
              </label>
              <div className="flex justify-center gap-2 my-4">
                {[1, 2, 3, 4, 5].map(star => renderStar(star))}
              </div>
              <p
                className={`text-lg font-semibold ${
                  displayRating === 0
                    ? "text-gray-500 dark:text-gray-400"
                    : displayRating <= 2
                      ? "text-red-600 dark:text-red-400"
                      : displayRating === 3
                        ? "text-yellow-600 dark:text-yellow-400"
                        : "text-green-600 dark:text-green-400"
                }`}
              >
                {getRatingLabel(displayRating)}
                {displayRating > 0 && ` (${displayRating}/5)`}
              </p>
            </div>

            {/* Message Textarea (Optional) */}
            <div>
              <label
                htmlFor="feedback-message"
                className="block text-sm font-medium text-indigo-900 dark:text-indigo-50 mb-2"
              >
                Additional comments (optional)
              </label>
              <textarea
                id="feedback-message"
                value={message}
                onChange={e => setMessage(e.target.value)}
                disabled={isSubmitting}
                placeholder="Tell us more about your experience..."
                rows={4}
                className="w-full px-4 py-3 bg-white dark:bg-indigo-950 border-2 border-indigo-300 dark:border-indigo-700 rounded-lg focus:outline-none focus:ring-3 focus:ring-focus focus:border-indigo-500 text-indigo-900 dark:text-indigo-50 placeholder-indigo-400 dark:placeholder-indigo-500 transition-colors resize-none disabled:opacity-50"
              />
              <p className="mt-1 text-xs text-indigo-600 dark:text-indigo-400">
                {message.length} characters
              </p>
            </div>

            {/* Status Messages */}
            {submitStatus === "success" && (
              <div className="p-3 bg-green-100 dark:bg-green-900/30 border border-green-300 dark:border-green-700 rounded-lg">
                <p className="text-sm font-medium text-green-800 dark:text-green-200">
                  ✓ Thank you for your feedback! Your response has been submitted.
                </p>
              </div>
            )}

            {submitStatus === "error" && (
              <div className="p-3 bg-red-100 dark:bg-red-900/30 border border-red-300 dark:border-red-700 rounded-lg">
                <p className="text-sm font-medium text-red-800 dark:text-red-200">
                  ✗ {errorMessage || "Failed to submit feedback. Please select a rating."}
                </p>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex gap-3 pt-2">
              <button
                type="button"
                onClick={handleClose}
                disabled={isSubmitting}
                className="flex-1 px-4 py-3 bg-indigo-100 hover:bg-indigo-200 active:bg-indigo-300 dark:bg-indigo-800 dark:hover:bg-indigo-700 dark:active:bg-indigo-600 text-indigo-900 dark:text-indigo-50 rounded-lg transition-colors font-medium focus:outline-none focus:ring-3 focus:ring-focus min-h-[44px] disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting || rating === 0}
                className="flex-1 px-4 py-3 bg-yellow-500 hover:bg-yellow-600 active:bg-yellow-700 dark:bg-yellow-600 dark:hover:bg-yellow-500 dark:active:bg-yellow-400 text-white rounded-lg transition-colors font-medium focus:outline-none focus:ring-3 focus:ring-focus min-h-[44px] disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSubmitting ? "Sending..." : "Submit Feedback"}
              </button>
            </div>
          </form>
        </div>
      </div>
    </>
  );
};
