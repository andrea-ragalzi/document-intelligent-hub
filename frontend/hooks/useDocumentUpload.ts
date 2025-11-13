"use client";

import { useState, useCallback } from "react";
import type { ChangeEvent, FormEvent } from "react";
import type { AlertState } from "@/lib/types";
import { API_BASE_URL } from "@/lib/constants";

interface UseUploadResult {
  file: File | null;
  setFile: React.Dispatch<React.SetStateAction<File | null>>;
  isUploading: boolean;
  uploadAlert: AlertState;
  handleFileChange: (e: ChangeEvent<HTMLInputElement>) => void;
  handleUpload: (e: FormEvent, currentUserId: string) => Promise<void>;
  documentsUploaded: number; // Track number of successful uploads
}

export const useDocumentUpload = (): UseUploadResult => {
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [documentsUploaded, setDocumentsUploaded] = useState<number>(0);
  const [uploadAlert, setUploadAlert] = useState<AlertState>({
    message: "Enter a User ID and upload a PDF.",
    type: "info",
  });

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      if (selectedFile.type !== "application/pdf") {
        setUploadAlert({
          message: "Only PDF files are supported.",
          type: "error",
        });
        setFile(null);
      } else {
        setFile(selectedFile);
        setUploadAlert({
          message: selectedFile.name + " ready for indexing.",
          type: "info",
        });
      }
    } else {
      setFile(null);
      setUploadAlert({ message: "No file selected.", type: "info" });
    }
  };

  const handleUpload = useCallback(
    async (e: FormEvent, currentUserId: string) => {
      e.preventDefault();
      if (!file || !currentUserId) {
        setUploadAlert({
          message: "Select a PDF file and make sure User ID is available.",
          type: "error",
        });
        return;
      }

      setIsUploading(true);
      setUploadAlert({
        message: "Uploading and indexing in progress...",
        type: "info",
      });

      const formData = new FormData();
      formData.append("file", file);
      formData.append("user_id", currentUserId);

      try {
        const response = await fetch(`${API_BASE_URL}/upload/`, {
          method: "POST",
          body: formData,
        });

        const data = await response.json();

        if (response.ok) {
          setUploadAlert({
            message: `${data.message} Chunks indexed: ${data.chunks_indexed}. You can now chat!`,
            type: "success",
          });
          setFile(null);
          setDocumentsUploaded((prev) => prev + 1); // Increment upload counter

          // Trigger document status refresh
          window.dispatchEvent(new Event("refreshDocumentStatus"));

          const fileInput = document.getElementById(
            "pdf-upload"
          ) as HTMLInputElement;
          if (fileInput) fileInput.value = "";
        } else {
          setUploadAlert({
            message: `Upload error: ${data.detail || "Unknown error"}`,
            type: "error",
          });
        }
      } catch (error) {
        console.error("Upload Error:", error);
        setUploadAlert({
          message: `Network error: Unable to connect to backend.`,
          type: "error",
        });
      } finally {
        setIsUploading(false);
      }
    },
    [file]
  );

  return {
    file,
    setFile,
    isUploading,
    uploadAlert,
    handleFileChange,
    handleUpload,
    documentsUploaded,
  };
};
