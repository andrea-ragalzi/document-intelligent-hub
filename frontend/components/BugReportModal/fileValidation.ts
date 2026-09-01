/**
 * File validation utilities for BugReportModal
 */

const MAX_FILE_SIZE = 5 * 1024 * 1024;

const ALLOWED_TYPES = ["image/png", "image/jpeg", "image/webp"];

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
      error: `Screenshot too large. Maximum size is 5MB, got ${(fileSize / 1024 / 1024).toFixed(2)}MB`,
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
      error: "Only PNG, JPEG, and WebP screenshots are allowed",
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
  return ALLOWED_TYPES.includes(fileType);
}
