import { Upload, RefreshCw } from "lucide-react";
import { FormEvent, ChangeEvent, RefObject } from "react";
import { UploadProgress } from "../UploadProgress";
import { AlertMessage } from "../AlertMessage";
import type { AlertState } from "@/lib/types";

interface UploadProgressState {
  progress: number;
  status: "uploading" | "processing" | "complete" | "error";
  message?: string;
  estimatedTime?: string;
  chunksProcessed?: number;
  totalChunks?: number;
  currentPhase?: "upload" | "embedding";
}

interface DocumentUploadSectionProps {
  file: File | null;
  isUploading: boolean;
  userId: string | null;
  dragActive: boolean;
  uploadAlert: AlertState;
  statusAlert: AlertState | null;
  uploadProgress?: UploadProgressState;
  fileInputRef: RefObject<HTMLInputElement | null>;
  onFileChange: (e: ChangeEvent<HTMLInputElement>) => void;
  onUpload: (e: FormEvent) => void;
  onDragEnter: (e: React.DragEvent) => void;
  onDragLeave: (e: React.DragEvent) => void;
  onDragOver: (e: React.DragEvent) => void;
  onDrop: (e: React.DragEvent) => void;
}

export const DocumentUploadSection: React.FC<DocumentUploadSectionProps> = ({
  file,
  isUploading,
  userId,
  dragActive,
  uploadAlert,
  statusAlert,
  uploadProgress,
  fileInputRef,
  onFileChange,
  onUpload,
  onDragEnter,
  onDragLeave,
  onDragOver,
  onDrop,
}) => {
  return (
    <form onSubmit={onUpload} className="space-y-4">
      <div
        onDragEnter={onDragEnter}
        onDragLeave={onDragLeave}
        onDragOver={onDragOver}
        onDrop={onDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`relative border-2 border-dashed rounded-lg p-8 text-center transition-all duration-300 cursor-pointer ${
          dragActive
            ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20"
            : "border-gray-300 dark:border-gray-600 hover:border-blue-500 dark:hover:border-blue-500"
        }`}
      >
        <Upload
          size={40}
          className={`mx-auto mb-3 transition-colors ${
            dragActive ? "text-blue-600" : "text-blue-500"
          }`}
        />
        <p className="font-semibold text-gray-900 dark:text-white">
          {dragActive ? "Drop PDF here" : "Drag & drop PDF or click to browse"}
        </p>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          Document will be automatically indexed (max 10MB)
        </p>
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf"
          onChange={onFileChange}
          className="hidden"
          disabled={isUploading}
        />
        {file && (
          <p className="mt-3 text-blue-600 dark:text-blue-400 font-medium">
            Selected: <strong>{file.name}</strong>
          </p>
        )}
      </div>

      <button
        type="submit"
        disabled={isUploading || !file || !userId}
        className={`w-full flex justify-center items-center py-3 px-4 text-sm font-bold rounded-lg shadow-lg transition duration-200 transform hover:scale-[1.01] ${
          isUploading || !file || !userId
            ? "bg-gray-300 text-gray-600 cursor-not-allowed dark:bg-gray-600 dark:text-gray-300"
            : "bg-blue-600 text-white hover:bg-blue-700 hover:shadow-xl"
        }`}
      >
        {isUploading ? (
          <>
            <RefreshCw size={18} className="animate-spin mr-2" />
            Upload & Indexing in Progress...
          </>
        ) : (
          <>
            <Upload size={18} className="mr-2" />
            Upload & Index Document
          </>
        )}
      </button>

      {/* Upload Progress */}
      {isUploading && uploadProgress && (
        <UploadProgress
          isUploading={isUploading}
          progress={uploadProgress.progress}
          status={uploadProgress.status}
          message={uploadProgress.message}
          estimatedTime={uploadProgress.estimatedTime}
          chunksProcessed={uploadProgress.chunksProcessed}
          totalChunks={uploadProgress.totalChunks}
          currentPhase={uploadProgress.currentPhase}
        />
      )}

      {/* Alerts */}
      <div className="space-y-2">
        {statusAlert && <AlertMessage alert={statusAlert} />}
        <AlertMessage alert={uploadAlert} />
      </div>
    </form>
  );
};
