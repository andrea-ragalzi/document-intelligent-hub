import { Loader, CheckCircle2, XCircle } from "lucide-react";

interface UploadProgressProps {
  isUploading: boolean;
  progress: number; // 0-100
  status: "uploading" | "processing" | "complete" | "error";
  message?: string;
  estimatedTime?: string;
  chunksProcessed?: number;
  totalChunks?: number;
}

export const UploadProgress: React.FC<UploadProgressProps> = ({
  isUploading,
  progress,
  status,
  message,
  estimatedTime,
  chunksProcessed,
  totalChunks,
}) => {
  if (!isUploading && status !== "complete" && status !== "error") {
    return null;
  }

  const getStatusIcon = () => {
    switch (status) {
      case "complete":
        return <CheckCircle2 size={20} className="text-green-500" />;
      case "error":
        return <XCircle size={20} className="text-red-500" />;
      default:
        return <Loader size={20} className="animate-spin text-blue-500" />;
    }
  };

  const getStatusColor = () => {
    switch (status) {
      case "complete":
        return "bg-green-500";
      case "error":
        return "bg-red-500";
      case "processing":
        return "bg-blue-500";
      default:
        return "bg-blue-400";
    }
  };

  const getStatusText = () => {
    switch (status) {
      case "uploading":
        return "Uploading document...";
      case "processing":
        return "Generating embeddings...";
      case "complete":
        return "✅ Upload complete!";
      case "error":
        return "❌ Upload failed";
      default:
        return "Processing...";
    }
  };

  return (
    <div className="mt-4 p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 shadow-sm">
      {/* Status Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-2">
          {getStatusIcon()}
          <span className="text-sm font-semibold text-gray-700 dark:text-gray-200">
            {getStatusText()}
          </span>
        </div>
        {estimatedTime && status === "processing" && (
          <span className="text-xs text-gray-500 dark:text-gray-400">
            ~{estimatedTime} remaining
          </span>
        )}
      </div>

      {/* Progress Bar */}
      <div className="relative w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
        <div
          className={`absolute top-0 left-0 h-full ${getStatusColor()} transition-all duration-500 ease-out`}
          style={{ width: `${progress}%` }}
        >
          {/* Animated shimmer effect */}
          {status === "processing" && (
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent animate-shimmer" />
          )}
        </div>
      </div>

      {/* Progress Details */}
      <div className="flex items-center justify-between mt-2 text-xs text-gray-600 dark:text-gray-400">
        <span>
          {chunksProcessed !== undefined && totalChunks !== undefined ? (
            <>
              {chunksProcessed.toLocaleString()} /{" "}
              {totalChunks.toLocaleString()} chunks
            </>
          ) : (
            <>{progress}%</>
          )}
        </span>
        {message && (
          <span className="text-right max-w-xs truncate">{message}</span>
        )}
      </div>
    </div>
  );
};
