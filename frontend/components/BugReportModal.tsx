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

interface BugReportModalProps {
  isOpen: boolean;
  onClose: () => void;
  conversationId?: string | null;
  userId?: string | null;
}

export const BugReportModal: React.FC<BugReportModalProps> = ({
  isOpen,
  onClose,
  conversationId,
  userId,
}) => {
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
      const formData = createBugReportFormData(userId, description, conversationId, attachedFile);

      console.log("Sending bug report with FormData");
      await submitBugReport(formData);

      setSubmitStatus("success");
      resetForm();

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
          <BugReportModalHeader isSubmitting={isSubmitting} onClose={handleClose} />

          {/* Form */}
          <form onSubmit={handleSubmit} className="p-6 space-y-4">
            {/* Info Banner */}
            <BugReportModalInfo conversationId={conversationId} />

            {/* Description Textarea */}
            <div>
              <label
                htmlFor="bug-description"
                className="block text-sm font-medium text-indigo-900 dark:text-indigo-50 mb-2"
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
                className="w-full px-4 py-3 bg-white dark:bg-indigo-950 border-2 border-indigo-300 dark:border-indigo-700 rounded-lg focus:outline-none focus:ring-3 focus:ring-focus focus:border-indigo-500 text-indigo-900 dark:text-indigo-50 placeholder-indigo-400 dark:placeholder-indigo-500 transition-colors resize-none disabled:opacity-50"
              />
              <div className="mt-2 flex justify-between items-center">
                <p className="text-xs text-indigo-600 dark:text-indigo-400">
                  📧 Your report will be sent to the support team via email.
                </p>
                <p
                  className={`text-xs font-medium ${
                    description.trim().length < 10
                      ? "text-red-600 dark:text-red-400"
                      : "text-green-600 dark:text-green-400"
                  }`}
                >
                  {description.trim().length} / 10 chars
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

            {/* Technical Details Preview (Collapsible) */}
            <details className="group">
              <summary className="cursor-pointer select-none flex items-center gap-2 p-3 bg-gray-50 dark:bg-gray-900/30 rounded-lg border border-gray-200 dark:border-gray-700 hover:bg-gray-100 dark:hover:bg-gray-900/50 transition-colors">
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  🔍 Technical Details (click to expand)
                </span>
                <span className="ml-auto text-gray-500 dark:text-gray-400 text-xs group-open:rotate-180 transition-transform">
                  ▼
                </span>
              </summary>
              <div className="mt-2 p-4 bg-gray-50 dark:bg-gray-900/30 rounded-lg border border-gray-200 dark:border-gray-700 space-y-2">
                <div className="text-xs space-y-1">
                  <div className="flex justify-between">
                    <span className="font-semibold text-gray-700 dark:text-gray-300">User ID:</span>
                    <code className="text-gray-600 dark:text-gray-400 break-all max-w-[60%] text-right">
                      {userId || "anonymous"}
                    </code>
                  </div>
                  <div className="flex justify-between">
                    <span className="font-semibold text-gray-700 dark:text-gray-300">
                      Conversation:
                    </span>
                    <code className="text-gray-600 dark:text-gray-400 break-all max-w-[60%] text-right">
                      {conversationId || "N/A"}
                    </code>
                  </div>
                  <div className="flex justify-between">
                    <span className="font-semibold text-gray-700 dark:text-gray-300">
                      Timestamp:
                    </span>
                    <code className="text-gray-600 dark:text-gray-400">
                      {new Date().toLocaleString()}
                    </code>
                  </div>
                  <div className="flex justify-between items-start">
                    <span className="font-semibold text-gray-700 dark:text-gray-300">Browser:</span>
                    <code className="text-gray-600 dark:text-gray-400 text-right text-[10px] max-w-[60%] break-all leading-tight">
                      {navigator.userAgent.split(" ").slice(0, 3).join(" ")}...
                    </code>
                  </div>
                </div>
                <p className="text-[11px] text-gray-500 dark:text-gray-400 mt-3 pt-2 border-t border-gray-300 dark:border-gray-600">
                  💡 These details help us reproduce and fix the issue faster.
                </p>
              </div>
            </details>

            {/* Status Messages */}
            <BugReportStatusMessages submitStatus={submitStatus} errorMessage={errorMessage} />

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
                disabled={
                  isSubmitting ||
                  description.trim().length < 10 ||
                  (attachedFile !== null && attachedFile.size > 10 * 1024 * 1024)
                }
                className="flex-1 px-4 py-3 bg-red-600 hover:bg-red-700 active:bg-red-800 dark:bg-red-600 dark:hover:bg-red-500 dark:active:bg-red-400 text-white rounded-lg transition-colors font-medium focus:outline-none focus:ring-3 focus:ring-focus min-h-[44px] disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSubmitting ? "Sending..." : "Submit Report"}
              </button>
            </div>
          </form>
        </div>
      </div>
    </>
  );
};
