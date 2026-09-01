import { X } from "lucide-react";
import { useState } from "react";
import { useAuth } from "@/contexts/AuthContext";

interface FeedbackModalProps {
  isOpen: boolean;
  onClose: () => void;
  conversationId?: string | null;
}

export const FeedbackModal: React.FC<FeedbackModalProps> = ({ isOpen, onClose }) => {
  const { getIdToken } = useAuth();
  const [message, setMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  if (!isOpen) return null;

  const close = () => {
    if (isSubmitting) return;
    setMessage("");
    setErrorMessage("");
    onClose();
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    const trimmedMessage = message.trim();
    if (!trimmedMessage) {
      setErrorMessage("Please enter your feedback.");
      return;
    }

    setIsSubmitting(true);
    setErrorMessage("");
    try {
      const token = await getIdToken();
      if (!token) throw new Error("Please sign in again before submitting feedback.");
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/feedback`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ message: trimmedMessage }),
      });
      if (!response.ok) throw new Error("Unable to submit feedback. Please try again later.");
      setMessage("");
      onClose();
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Unable to submit feedback.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <button
        type="button"
        className="absolute inset-0 cursor-default bg-black/60"
        aria-label="Close feedback form"
        onClick={close}
      />
      <div className="relative w-full max-w-lg rounded-xl border border-line/20 bg-surface shadow-xl">
        <div className="flex items-center justify-between border-b border-line/15 p-6">
          <h2 className="text-xl font-semibold text-ink">Give feedback</h2>
          <button
            type="button"
            onClick={close}
            disabled={isSubmitting}
            aria-label="Close feedback form"
          >
            <X size={24} className="text-muted" />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4 p-6">
          <label htmlFor="feedback-message" className="block text-sm font-medium text-ink">
            Your feedback
          </label>
          <textarea
            id="feedback-message"
            value={message}
            onChange={event => setMessage(event.target.value)}
            disabled={isSubmitting}
            required
            maxLength={1000}
            rows={5}
            className="ui-input w-full resize-none rounded-lg px-4 py-3 focus:outline-none focus:ring-3 focus:ring-focus"
          />
          <p className="text-right text-xs text-muted">{message.length} / 1,000</p>
          {errorMessage && <p className="text-sm text-danger">{errorMessage}</p>}
          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={close}
              disabled={isSubmitting}
              className="ui-secondary-action flex-1 rounded-lg px-4 py-3 font-medium"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting || !message.trim()}
              className="ui-primary-action flex-1 rounded-lg px-4 py-3 font-medium disabled:opacity-50"
            >
              {isSubmitting ? "Sending..." : "Submit feedback"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
