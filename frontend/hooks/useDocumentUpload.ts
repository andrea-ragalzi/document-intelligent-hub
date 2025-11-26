"use client";

import { useState, useCallback } from "react";
import type { ChangeEvent, FormEvent } from "react";
import type { AlertState } from "@/lib/types";
import { API_BASE_URL } from "@/lib/constants";
import { useAuth } from "@/contexts/AuthContext";

interface UseUploadOptions {
  onSuccess?: () => void;
}

interface UseUploadResult {
  file: File | null;
  setFile: React.Dispatch<React.SetStateAction<File | null>>;
  isUploading: boolean;
  uploadAlert: AlertState;
  handleFileChange: (e: ChangeEvent<HTMLInputElement>) => void;
  handleUpload: (e: FormEvent, currentUserId: string) => Promise<void>;
  resetAlert: () => void;
  documentsUploaded: number;
  selectedLanguage: string;
  setSelectedLanguage: (lang: string) => void;
}

export const useDocumentUpload = (
  options?: UseUploadOptions
): UseUploadResult => {
  const { onSuccess } = options || {};
  const { getIdToken } = useAuth();
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [documentsUploaded, setDocumentsUploaded] = useState<number>(0);
  const [selectedLanguage, setSelectedLanguage] = useState<string>("en");
  const [uploadAlert, setUploadAlert] = useState<AlertState>({
    message: "Enter a User ID and upload a PDF.",
    type: "info",
  });

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      if (selectedFile.type === "application/pdf") {
        setFile(selectedFile);
        setUploadAlert({
          message: `${selectedFile.name} ready for indexing.`,
          type: "info",
        });
      } else {
        setUploadAlert({
          message: "Only PDF files are supported.",
          type: "error",
        });
        setFile(null);
      }
    } else {
      setFile(null);
      setUploadAlert({ message: "No file selected.", type: "info" });
    }
  };

  const handleUpload = useCallback(
    async (e: FormEvent, currentUserId: string) => {
      console.log("🔵 handleUpload called with:", {
        file: file?.name,
        currentUserId,
      });
      e.preventDefault();
      if (!file || !currentUserId) {
        console.log("❌ Missing file or userId:", {
          file: !!file,
          currentUserId,
        });
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

      // Send selected language
      formData.append("document_language", selectedLanguage.toUpperCase());

      console.log("📤 Sending upload request to:", `${API_BASE_URL}/upload/`);
      console.log("🌍 Selected language:", selectedLanguage.toUpperCase());

      try {
        // Get Firebase Auth token
        const token = await getIdToken();
        if (!token) {
          throw new Error("No authentication token available");
        }

        const response = await fetch(`${API_BASE_URL}/upload/`, {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
          },
          body: formData,
        });

        const data = await response.json();

        if (response.ok) {
          console.log("✅ Upload successful, emitting events...");
          console.log("📊 Response data:", data);

          setUploadAlert({
            message: `${data.message} Chunks indexed: ${data.chunks_indexed}. You can now chat!`,
            type: "success",
          });
          setFile(null);
          console.log("📁 File state cleared");
          setDocumentsUploaded((prev) => prev + 1); // Increment upload counter

          // Trigger document status refresh (for UI state updates)
          console.log("📡 Dispatching refreshDocumentStatus event");
          globalThis.dispatchEvent(new Event("refreshDocumentStatus"));

          // NOTE: Removed 'documentUploaded' event dispatch to prevent multiple refreshes
          // DocumentManager now handles refresh based on isUploading state change

          // Call onSuccess callback if provided
          if (onSuccess) {
            console.log("✅ Calling onSuccess callback");
            onSuccess();
          }

          // Clear file input
          const fileInput = document.getElementById(
            "pdf-upload"
          ) as HTMLInputElement;
          if (fileInput) {
            fileInput.value = "";
            console.log("🔄 File input cleared");
          }
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
    [file, onSuccess, selectedLanguage]
  );

  const resetAlert = useCallback(() => {
    setUploadAlert({
      message: "Enter a User ID and upload a PDF.",
      type: "info",
    });
  }, []);

  return {
    file,
    setFile,
    isUploading,
    uploadAlert,
    handleFileChange,
    handleUpload,
    resetAlert,
    documentsUploaded,
    selectedLanguage,
    setSelectedLanguage,
  };
};
