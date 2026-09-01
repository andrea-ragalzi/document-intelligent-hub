import { Paperclip, X } from "lucide-react";
import Image from "next/image";

interface BugReportFileAttachmentProps {
  attachedFile: File | null;
  filePreview: string | null;
  isSubmitting: boolean;
  onFileSelect: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onRemoveFile: () => void;
}

export const BugReportFileAttachment: React.FC<BugReportFileAttachmentProps> = ({
  attachedFile,
  filePreview,
  isSubmitting,
  onFileSelect,
  onRemoveFile,
}) => {
  return (
    <div>
      <label htmlFor="bug-file-input" className="block text-sm font-medium text-ink mb-2">
        Attach screenshot (optional, max 5MB)
      </label>
      <p className="text-xs text-gray-600 dark:text-gray-400 mb-2">Supported: PNG, JPEG, WebP</p>

      {/* File Input Button */}
      {!attachedFile && (
        <label
          htmlFor="bug-file-input"
          className="flex items-center gap-2 px-4 py-2 bg-raised text-accent rounded-lg hover:bg-surface-hover transition-colors cursor-pointer w-fit"
        >
          <Paperclip size={18} />
          <span className="text-sm font-medium">Choose File</span>
          <input
            id="bug-file-input"
            type="file"
            accept="image/png,image/jpeg,image/webp"
            onChange={onFileSelect}
            disabled={isSubmitting}
            className="hidden"
          />
        </label>
      )}

      {/* File Preview/Info */}
      {attachedFile && (
        <div className="space-y-2">
          {/* File info card */}
          <div className="flex items-start gap-3 p-3 bg-raised rounded-lg border border-line/15">
            <Paperclip size={20} className="text-accent flex-shrink-0 mt-0.5" />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-ink truncate">{attachedFile.name}</p>
              <p
                className={`text-xs mt-0.5 ${
                  attachedFile.size > 5 * 1024 * 1024
                    ? "text-red-600 dark:text-red-400 font-semibold"
                    : "text-accent"
                }`}
              >
                {(attachedFile.size / 1024 / 1024).toFixed(2)} MB
                {attachedFile.size > 5 * 1024 * 1024 && " - Too large! Max 5MB"}
              </p>
            </div>
            <button
              type="button"
              onClick={onRemoveFile}
              disabled={isSubmitting}
              className="text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 transition-colors disabled:opacity-50"
            >
              <X size={18} />
            </button>
          </div>

          {/* Screenshot preview */}
          {filePreview && attachedFile && (
            <div className="relative w-full max-h-48 overflow-hidden rounded-lg border border-line/20">
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
              ) : null}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
