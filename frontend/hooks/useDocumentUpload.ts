"use client";

import { useCallback, useRef, useState } from "react";
import type { ChangeEvent, FormEvent } from "react";
import type { AlertState } from "@/lib/types";
import { API_BASE_URL } from "@/lib/constants";
import { useAuth } from "@/contexts/AuthContext";

export type DuplicateAction = "replace" | "rename" | "skip";

interface UseUploadOptions {
  onSuccess?: () => void;
}

interface UseUploadResult {
  files: File[];
  isUploading: boolean;
  uploadAlert: AlertState;
  pendingDuplicate: File | null;
  handleFileChange: (event: ChangeEvent<HTMLInputElement>) => void;
  handleUpload: (
    event: FormEvent,
    currentUserId: string,
    existingFilenames: string[]
  ) => Promise<void>;
  resolveDuplicate: (action: DuplicateAction) => Promise<void>;
  resetAlert: () => void;
  documentsUploaded: number;
  selectedLanguage: string;
  setSelectedLanguage: (language: string) => void;
}

interface UploadSummary {
  uploaded: number;
  skipped: number;
  failed: number;
}

export const useDocumentUpload = (options?: UseUploadOptions): UseUploadResult => {
  const { onSuccess } = options || {};
  const { getIdToken } = useAuth();
  const [files, setFiles] = useState<File[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [documentsUploaded, setDocumentsUploaded] = useState(0);
  const [selectedLanguage, setSelectedLanguage] = useState("en");
  const [pendingDuplicate, setPendingDuplicate] = useState<File | null>(null);
  const [uploadAlert, setUploadAlert] = useState<AlertState>({
    message: "Select a PDF to upload.",
    type: "info",
  });

  const queueRef = useRef<File[]>([]);
  const currentIndexRef = useRef(0);
  const knownFilenamesRef = useRef<Set<string>>(new Set());
  const resolutionsRef = useRef<Map<number, DuplicateAction>>(new Map());
  const summaryRef = useRef<UploadSummary>({ uploaded: 0, skipped: 0, failed: 0 });
  const currentUserIdRef = useRef<string | null>(null);

  const finishQueue = useCallback(() => {
    const { uploaded, skipped, failed } = summaryRef.current;
    const parts = [
      uploaded > 0 ? `${uploaded} uploaded` : null,
      skipped > 0 ? `${skipped} skipped` : null,
      failed > 0 ? `${failed} failed` : null,
    ].filter(Boolean);

    setFiles([]);
    setPendingDuplicate(null);
    setIsUploading(false);
    setUploadAlert({
      message: parts.length ? `Upload complete: ${parts.join(", ")}.` : "No files were uploaded.",
      type: failed > 0 ? "error" : "success",
    });
    globalThis.dispatchEvent(new Event("refreshDocumentStatus"));
    if (uploaded > 0) onSuccess?.();
  }, [onSuccess]);

  const processQueue = useCallback(async () => {
    const currentUserId = currentUserIdRef.current;
    if (!currentUserId) return;

    while (currentIndexRef.current < queueRef.current.length) {
      const index = currentIndexRef.current;
      const file = queueRef.current[index];
      const existingName = knownFilenamesRef.current.has(file.name);
      const action = resolutionsRef.current.get(index);

      if (existingName && !action) {
        setIsUploading(false);
        setPendingDuplicate(file);
        setUploadAlert({
          message: `“${file.name}” already exists. Choose how to continue.`,
          type: "info",
        });
        return;
      }

      if (action === "skip") {
        summaryRef.current.skipped += 1;
        currentIndexRef.current += 1;
        continue;
      }

      setIsUploading(true);
      setUploadAlert({
        message: `Uploading ${index + 1} of ${queueRef.current.length}: ${file.name}`,
        type: "info",
      });

      try {
        const token = await getIdToken();
        if (!token) throw new Error("No authentication token available");

        const formData = new FormData();
        formData.append("file", file);
        formData.append("document_language", selectedLanguage.toUpperCase());
        if (action === "replace" || action === "rename") {
          formData.append("duplicate_action", action);
        }

        const response = await fetch(`${API_BASE_URL}/upload/`, {
          method: "POST",
          headers: { Authorization: `Bearer ${token}` },
          body: formData,
        });
        const data = await response.json().catch(() => ({}));

        if (response.status === 409) {
          resolutionsRef.current.delete(index);
          setIsUploading(false);
          setPendingDuplicate(file);
          setUploadAlert({
            message: `“${file.name}” now conflicts with an existing document. Choose how to continue.`,
            type: "info",
          });
          return;
        }

        if (!response.ok) {
          summaryRef.current.failed += 1;
          setUploadAlert({
            message: `${file.name}: ${data.detail || "Upload failed."}`,
            type: "error",
          });
          currentIndexRef.current += 1;
          continue;
        }

        const finalFilename =
          typeof data.filename === "string" && data.filename ? data.filename : file.name;
        knownFilenamesRef.current.add(finalFilename);
        summaryRef.current.uploaded += 1;
        setDocumentsUploaded(previous => previous + 1);
        currentIndexRef.current += 1;
      } catch {
        summaryRef.current.failed += 1;
        setUploadAlert({
          message: `${file.name}: unable to connect to the backend.`,
          type: "error",
        });
        currentIndexRef.current += 1;
      }
    }

    finishQueue();
  }, [finishQueue, getIdToken, selectedLanguage]);

  const handleFileChange = useCallback((event: ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = Array.from(event.target.files || []);
    const pdfFiles = selectedFiles.filter(
      file => file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf")
    );

    setPendingDuplicate(null);
    resolutionsRef.current.clear();
    setFiles(pdfFiles);
    if (!pdfFiles.length) {
      setUploadAlert({ message: "Only PDF files are supported.", type: "error" });
      return;
    }

    const ignoredCount = selectedFiles.length - pdfFiles.length;
    setUploadAlert({
      message:
        ignoredCount > 0
          ? `${pdfFiles.length} PDF${pdfFiles.length === 1 ? "" : "s"} selected; ${ignoredCount} non-PDF file${ignoredCount === 1 ? " was" : "s were"} ignored.`
          : `${pdfFiles.length} PDF${pdfFiles.length === 1 ? "" : "s"} ready for indexing.`,
      type: "info",
    });
  }, []);

  const handleUpload = useCallback(
    async (event: FormEvent, currentUserId: string, existingFilenames: string[]) => {
      event.preventDefault();
      if (!files.length || !currentUserId) {
        setUploadAlert({
          message: "Select a PDF to upload.",
          type: "error",
        });
        return;
      }

      queueRef.current = files;
      currentIndexRef.current = 0;
      currentUserIdRef.current = currentUserId;
      knownFilenamesRef.current = new Set(existingFilenames);
      resolutionsRef.current.clear();
      summaryRef.current = { uploaded: 0, skipped: 0, failed: 0 };
      await processQueue();
    },
    [files, processQueue]
  );

  const resolveDuplicate = useCallback(
    async (action: DuplicateAction) => {
      if (!pendingDuplicate) return;
      resolutionsRef.current.set(currentIndexRef.current, action);
      setPendingDuplicate(null);
      await processQueue();
    },
    [pendingDuplicate, processQueue]
  );

  const resetAlert = useCallback(() => {
    setUploadAlert({ message: "Select a PDF to upload.", type: "info" });
  }, []);

  return {
    files,
    isUploading,
    uploadAlert,
    pendingDuplicate,
    handleFileChange,
    handleUpload,
    resolveDuplicate,
    resetAlert,
    documentsUploaded,
    selectedLanguage,
    setSelectedLanguage,
  };
};
