/**
 * File validation utilities for BugReportModal
 */

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

const ALLOWED_TYPES = [
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

export interface FileValidationError {
  isValid: false;
  error: string;
}

export interface FileValidationSuccess {
  isValid: true;
}

export type FileValidationResult = FileValidationError | FileValidationSuccess;

/**
 * Validates file size
 */
function validateFileSize(fileSize: number): FileValidationResult {
  if (fileSize > MAX_FILE_SIZE) {
    return {
      isValid: false,
      error: `File too large. Maximum size is 10MB, got ${(fileSize / 1024 / 1024).toFixed(2)}MB`,
    };
  }
  return { isValid: true };
}

/**
 * Validates file type
 */
function validateFileType(fileType: string): FileValidationResult {
  if (!ALLOWED_TYPES.includes(fileType)) {
    return {
      isValid: false,
      error: "Only images, PDF, videos, and compressed files (ZIP, RAR, 7z, TAR.GZ) are allowed",
    };
  }
  return { isValid: true };
}

/**
 * Validates a file for bug report attachment
 */
export function validateFile(file: File): FileValidationResult {
  const sizeValidation = validateFileSize(file.size);
  if (!sizeValidation.isValid) {
    return sizeValidation;
  }

  return validateFileType(file.type);
}

/**
 * Checks if file type supports preview
 */
export function supportsPreview(fileType: string): boolean {
  return fileType.startsWith("image/") || fileType.startsWith("video/");
}
