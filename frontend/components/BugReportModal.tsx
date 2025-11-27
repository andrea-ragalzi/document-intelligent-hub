import { Bug, Paperclip, X } from "lucide-react";
import { useState } from "react";
import Image from "next/image";

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
  const [description, setDescription] = useState("");
  const [attachedFile, setAttachedFile] = useState<File | null>(null);
  const [filePreview, setFilePreview] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitStatus, setSubmitStatus] = useState<
    "idle" | "success" | "error"
  >("idle");
  const [errorMessage, setErrorMessage] = useState("");

  if (!isOpen) return null;

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate file size (max 10MB)
    const maxSize = 10 * 1024 * 1024;
    if (file.size > maxSize) {
      setErrorMessage(
        `File too large. Maximum size is 10MB, got ${(
          file.size /
          1024 /
          1024
        ).toFixed(2)}MB`
      );
      setSubmitStatus("error");
      return;
    }

    // Validate file type
    const allowedTypes = [
      "image/png",
      "image/jpeg",
      "image/jpg",
      "image/gif",
      "application/pdf",
      "video/mp4",
      "video/webm",
      "video/quicktime",
      "video/x-msvideo",
      "application/zip",
      "application/x-zip-compressed",
      "application/x-rar-compressed",
      "application/x-rar",
      "application/x-7z-compressed",
      "application/gzip",
      "application/x-gzip",
      "application/x-tar",
      "application/x-compressed-tar",
    ];
    if (!allowedTypes.includes(file.type)) {
      setErrorMessage(
        "Only images, PDF, videos, and compressed files (ZIP, RAR, 7z, TAR.GZ) are allowed"
      );
      setSubmitStatus("error");
      return;
    }

    setAttachedFile(file);
    setSubmitStatus("idle");
    setErrorMessage("");

    // Create preview for images and videos
    if (file.type.startsWith("image/") || file.type.startsWith("video/")) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setFilePreview(reader.result as string);
      };
      reader.readAsDataURL(file);
    } else {
      setFilePreview(null);
    }
  };

  const handleRemoveFile = () => {
    setAttachedFile(null);
    setFilePreview(null);
    setErrorMessage("");
    // Reset file input
    const fileInput = document.getElementById(
      "bug-file-input"
    ) as HTMLInputElement;
    if (fileInput) fileInput.value = "";
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const trimmedDescription = description.trim();

    if (!trimmedDescription || trimmedDescription.length < 10) {
      setErrorMessage("Please provide at least 10 characters description");
      setSubmitStatus("error");
      return;
    }

    setIsSubmitting(true);
    setSubmitStatus("idle");
    setErrorMessage("");

    try {
      // Create FormData for multipart upload
      const formData = new FormData();
      formData.append("user_id", userId || "anonymous");
      formData.append("description", trimmedDescription);
      formData.append("timestamp", new Date().toISOString());
      formData.append("user_agent", navigator.userAgent);

      if (conversationId) {
        formData.append("conversation_id", conversationId);
      }

      if (attachedFile) {
        formData.append("attachment", attachedFile);
      }

      console.log("Sending bug report with FormData");

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/report-bug`,
        {
          method: "POST",
          body: formData,
          // Note: Don't set Content-Type header - browser will set it with boundary for multipart
        }
      );

      if (!response.ok) {
        // Handle specific error status codes
        if (response.status === 413) {
          throw new Error(
            "File too large. Maximum size is 10MB. Please try a smaller file or compress it."
          );
        }

        const errorData = await response
          .json()
          .catch(() => ({ detail: "Unknown error" }));
        console.error(
          "Bug report submission failed:",
          response.status,
          errorData
        );
        throw new Error(errorData.detail || "Failed to submit bug report");
      }

      setSubmitStatus("success");
      setDescription("");
      setAttachedFile(null);
      setFilePreview(null);

      // Close modal after 2 seconds
      setTimeout(() => {
        onClose();
        setSubmitStatus("idle");
      }, 2000);
    } catch (error) {
      console.error("Error submitting bug report:", error);
      setErrorMessage(
        error instanceof Error ? error.message : "Failed to submit bug report"
      );
      setSubmitStatus("error");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    if (!isSubmitting) {
      setDescription("");
      setAttachedFile(null);
      setFilePreview(null);
      setSubmitStatus("idle");
      setErrorMessage("");
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
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b-2 border-indigo-100 dark:border-indigo-800">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-red-100 dark:bg-red-900/30 rounded-lg">
                <Bug size={24} className="text-red-600 dark:text-red-400" />
              </div>
              <h2 className="text-xl font-semibold text-indigo-900 dark:text-indigo-50">
                Report a Bug
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
          <form onSubmit={handleSubmit} className="p-6 space-y-4">
            {/* Info Banner */}
            <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
              <p className="text-sm text-blue-900 dark:text-blue-200">
                <strong>ℹ️ What will be sent:</strong> Your bug description +
                optional file (image/video/PDF/archive) + technical context
                (User ID, Conversation ID, timestamp, browser info) will be
                emailed to our support team.
              </p>
            </div>

            {/* Conversation ID Display (if available) */}
            {conversationId && (
              <div className="p-3 bg-indigo-50 dark:bg-indigo-950 rounded-lg border border-indigo-200 dark:border-indigo-800">
                <p className="text-sm text-indigo-700 dark:text-indigo-300">
                  <span className="font-semibold">
                    📍 Current Conversation:
                  </span>{" "}
                  <code className="text-xs break-all">{conversationId}</code>
                </p>
              </div>
            )}

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
                onChange={(e) => setDescription(e.target.value)}
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
            <div>
              <label
                htmlFor="bug-file-input"
                className="block text-sm font-medium text-indigo-900 dark:text-indigo-50 mb-2"
              >
                Attach File (optional, max 10MB)
              </label>
              <p className="text-xs text-gray-600 dark:text-gray-400 mb-2">
                Supported: Images, PDF, Videos (MP4, WebM, MOV), Archives (ZIP,
                RAR, 7z, TAR.GZ)
              </p>

              {/* File Input Button */}
              {!attachedFile && (
                <label
                  htmlFor="bug-file-input"
                  className="flex items-center gap-2 px-4 py-2 bg-indigo-100 dark:bg-indigo-800 text-indigo-700 dark:text-indigo-200 rounded-lg hover:bg-indigo-200 dark:hover:bg-indigo-700 transition-colors cursor-pointer w-fit"
                >
                  <Paperclip size={18} />
                  <span className="text-sm font-medium">Choose File</span>
                  <input
                    id="bug-file-input"
                    type="file"
                    accept="image/png,image/jpeg,image/jpg,image/gif,application/pdf,video/mp4,video/webm,video/quicktime,video/x-msvideo,application/zip,application/x-zip-compressed,application/x-rar-compressed,application/x-7z-compressed,application/gzip,application/x-tar"
                    onChange={handleFileSelect}
                    disabled={isSubmitting}
                    className="hidden"
                  />
                </label>
              )}

              {/* File Preview/Info */}
              {attachedFile && (
                <div className="space-y-2">
                  {/* File info card */}
                  <div className="flex items-start gap-3 p-3 bg-indigo-50 dark:bg-indigo-950 rounded-lg border border-indigo-200 dark:border-indigo-700">
                    <Paperclip
                      size={20}
                      className="text-indigo-600 dark:text-indigo-400 flex-shrink-0 mt-0.5"
                    />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-indigo-900 dark:text-indigo-100 truncate">
                        {attachedFile.name}
                      </p>
                      <p
                        className={`text-xs mt-0.5 ${
                          attachedFile.size > 10 * 1024 * 1024
                            ? "text-red-600 dark:text-red-400 font-semibold"
                            : "text-indigo-600 dark:text-indigo-400"
                        }`}
                      >
                        {(attachedFile.size / 1024 / 1024).toFixed(2)} MB
                        {attachedFile.size > 10 * 1024 * 1024 &&
                          " - Too large! Max 10MB"}
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={handleRemoveFile}
                      disabled={isSubmitting}
                      className="text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 transition-colors disabled:opacity-50"
                    >
                      <X size={18} />
                    </button>
                  </div>

                  {/* Image/Video preview */}
                  {filePreview && attachedFile && (
                    <div className="relative w-full max-h-48 overflow-hidden rounded-lg border-2 border-indigo-200 dark:border-indigo-700">
                      {attachedFile.type.startsWith("image/") ? (
                        <div className="relative w-full h-48">
                          <Image
                            src={filePreview}
                            alt="File preview"
                            fill
                            className="object-contain"
                            unoptimized
                          />
                        </div>
                      ) : attachedFile.type.startsWith("video/") ? (
                        <video
                          src={filePreview}
                          controls
                          className="w-full h-auto object-contain"
                        >
                          Your browser does not support video playback.
                        </video>
                      ) : null}
                    </div>
                  )}
                </div>
              )}
            </div>

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
                    <span className="font-semibold text-gray-700 dark:text-gray-300">
                      User ID:
                    </span>
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
                    <span className="font-semibold text-gray-700 dark:text-gray-300">
                      Browser:
                    </span>
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
            {submitStatus === "success" && (
              <div className="p-3 bg-green-100 dark:bg-green-900/30 border border-green-300 dark:border-green-700 rounded-lg">
                <p className="text-sm font-medium text-green-800 dark:text-green-200">
                  ✓ Bug report submitted successfully! Email sent to support
                  team.
                </p>
              </div>
            )}

            {submitStatus === "error" && (
              <div className="p-3 bg-red-100 dark:bg-red-900/30 border border-red-300 dark:border-red-700 rounded-lg">
                <p className="text-sm font-medium text-red-800 dark:text-red-200">
                  ✗{" "}
                  {errorMessage ||
                    "Failed to submit report. Please provide at least 10 characters description."}
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
                disabled={
                  isSubmitting ||
                  description.trim().length < 10 ||
                  (attachedFile !== null &&
                    attachedFile.size > 10 * 1024 * 1024)
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
