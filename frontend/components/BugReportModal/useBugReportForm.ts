/**
 * Custom hook for bug report form state management
 */

import { useState } from "react";
import { validateFile, supportsPreview, type FileValidationResult } from "./fileValidation";

type SubmitStatus = "idle" | "success" | "error";

export function useBugReportForm() {
  const [description, setDescription] = useState("");
  const [attachedFile, setAttachedFile] = useState<File | null>(null);
  const [filePreview, setFilePreview] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitStatus, setSubmitStatus] = useState<SubmitStatus>("idle");
  const [errorMessage, setErrorMessage] = useState("");

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const validation: FileValidationResult = validateFile(file);
    if (!validation.isValid) {
      setErrorMessage(validation.error);
      setSubmitStatus("error");
      return;
    }

    setAttachedFile(file);
    setSubmitStatus("idle");
    setErrorMessage("");

    // Create preview for supported file types
    if (supportsPreview(file.type)) {
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
    const fileInput = document.getElementById("bug-file-input") as HTMLInputElement;
    if (fileInput) fileInput.value = "";
  };

  const resetForm = () => {
    setDescription("");
    setAttachedFile(null);
    setFilePreview(null);
    setSubmitStatus("idle");
    setErrorMessage("");
  };

  return {
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
  };
}
