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
      <label
        htmlFor="bug-file-input"
        className="block text-sm font-medium text-indigo-900 dark:text-indigo-50 mb-2"
      >
        Attach File (optional, max 10MB)
      </label>
      <p className="text-xs text-gray-600 dark:text-gray-400 mb-2">
        Supported: Images, PDF, Videos (MP4, WebM, MOV), Archives (ZIP, RAR, 7z, TAR.GZ)
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
                {attachedFile.size > 10 * 1024 * 1024 && " - Too large! Max 10MB"}
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
                <video src={filePreview} controls className="w-full h-auto object-contain">
                  Your browser does not support video playback.
                </video>
              ) : null}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
