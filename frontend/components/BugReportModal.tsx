// Removed unused imports
import { useBugReportForm } from "./BugReportModal/useBugReportForm";
import {
  validateDescription,
  createBugReportFormData,
  submitBugReport,
} from "./BugReportModal/bugReportApi";
import { BugReportModalHeader } from "./BugReportModal/BugReportModalHeader";
import { BugReportModalInfo } from "./BugReportModal/BugReportModalInfo";
import { BugReportFileAttachment } from "./BugReportModal/BugReportFileAttachment";
import { BugReportStatusMessages } from "./BugReportModal/BugReportStatusMessages";
import { useAuth } from "@/contexts/AuthContext";

interface BugReportModalProps {
  isOpen: boolean;
  onClose: () => void;
  conversationId?: string | null;
}

export const BugReportModal: React.FC<BugReportModalProps> = ({
  isOpen,
  onClose,
  conversationId,
}) => {
  const { getIdToken } = useAuth();
  const {
    description,
    setDescription,
    attachedFile,
    filePreview,
    isSubmitting,
    setIsSubmitting,
    submitStatus,
    setSubmitStatus,
    errorMessage,
    setErrorMessage,
    handleFileSelect,
    handleRemoveFile,
    resetForm,
  } = useBugReportForm();

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const validation = validateDescription(description);
    if (!validation.isValid) {
      setErrorMessage(validation.error!);
      setSubmitStatus("error");
      return;
    }

    setIsSubmitting(true);
    setSubmitStatus("idle");
    setErrorMessage("");

    try {
      const token = await getIdToken();
      if (!token) throw new Error("Please sign in again before submitting a report.");
      const formData = createBugReportFormData(description, conversationId, attachedFile);
      await submitBugReport(formData, token);

      resetForm();
      setSubmitStatus("success");

      // Close modal after 2 seconds
      setTimeout(() => {
        onClose();
        setSubmitStatus("idle");
      }, 2000);
    } catch (error) {
      console.error("Error submitting bug report:", error);
      setErrorMessage(error instanceof Error ? error.message : "Failed to submit bug report");
      setSubmitStatus("error");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    if (!isSubmitting) {
      resetForm();
      onClose();
    }
  };

  return (
    <>
      {/* Backdrop */}
      <div className="fixed inset-0 bg-black/60 z-50 transition-opacity" onClick={handleClose} />

      {/* Modal */}
      <div className="ui-modal-viewport z-50" onClick={handleClose}>
        <div className="flex min-h-full items-start justify-center p-3 sm:items-center sm:p-4">
          <div
            className="ui-modal-dialog flex w-full max-w-lg flex-col rounded-xl border border-line/20 bg-surface shadow-xl"
            onClick={e => e.stopPropagation()}
          >
            {/* Header */}
            <BugReportModalHeader isSubmitting={isSubmitting} onClose={handleClose} />

            {/* Form */}
            <form
              data-testid="bug-report-modal-body"
              onSubmit={handleSubmit}
              className="min-h-0 space-y-4 overflow-y-auto overscroll-contain p-4 sm:p-6"
            >
              {/* Info Banner */}
              <BugReportModalInfo />

              {/* Description Textarea */}
              <div>
                <label
                  htmlFor="bug-description"
                  className="block text-sm font-medium text-ink mb-2"
                >
                  Describe the bug *
                </label>
                <textarea
                  id="bug-description"
                  value={description}
                  onChange={e => setDescription(e.target.value)}
                  disabled={isSubmitting}
                  placeholder="What went wrong? Please include any error messages you saw..."
                  rows={6}
                  required
                  minLength={10}
                  maxLength={1500}
                  className="ui-input w-full px-4 py-3 rounded-lg focus:outline-none focus:ring-3 focus:ring-focus focus:border-focus transition-colors resize-none disabled:opacity-50"
                />
                <div className="mt-2 flex justify-between items-center">
                  <p className="text-xs text-muted">
                    Your report will be sent to the support team.
                  </p>
                  <p
                    className={`text-xs font-medium ${
                      description.trim().length < 10
                        ? "text-red-600 dark:text-red-400"
                        : "text-green-600 dark:text-green-400"
                    }`}
                  >
                    {description.trim().length} / 1,500 chars
                  </p>
                </div>
              </div>

              {/* File Attachment */}
              <BugReportFileAttachment
                attachedFile={attachedFile}
                filePreview={filePreview}
                isSubmitting={isSubmitting}
                onFileSelect={handleFileSelect}
                onRemoveFile={handleRemoveFile}
              />

              {/* Status Messages */}
              <BugReportStatusMessages submitStatus={submitStatus} errorMessage={errorMessage} />

              {/* Action Buttons */}
              <div className="sticky bottom-0 -mx-4 flex gap-3 border-t border-line/15 bg-surface px-4 pt-3 sm:-mx-6 sm:px-6">
                <button
                  type="button"
                  onClick={handleClose}
                  disabled={isSubmitting}
                  className="flex-1 px-4 py-3 bg-raised hover:bg-surface-hover active:bg-surface-hover text-ink rounded-lg transition-colors font-medium focus:outline-none focus:ring-3 focus:ring-focus min-h-[44px] disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={
                    isSubmitting ||
                    description.trim().length < 10 ||
                    (attachedFile !== null && attachedFile.size > 5 * 1024 * 1024)
                  }
                  className="flex-1 px-4 py-3 bg-red-600 hover:bg-red-700 active:bg-red-800 dark:bg-red-600 dark:hover:bg-red-500 dark:active:bg-red-400 text-white rounded-lg transition-colors font-medium focus:outline-none focus:ring-3 focus:ring-focus min-h-[44px] disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isSubmitting ? "Sending..." : "Submit Report"}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </>
  );
};
