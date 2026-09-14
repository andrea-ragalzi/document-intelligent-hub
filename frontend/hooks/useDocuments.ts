"use client";

import { useState, useEffect, useCallback } from "react";
import { API_BASE_URL } from "@/lib/constants";
import { fetchDocumentContent } from "@/lib/documentApi";
import { useAuth } from "@/contexts/AuthContext";

export interface Document {
  filename: string;
  chunks_count: number;
  language?: string;
  uploaded_at?: string;
  original_available?: boolean;
}

interface DocumentsResponse {
  documents: Document[];
  total_count: number;
  user_id: string;
}

interface UseDocumentsResult {
  documents: Document[];
  isLoading: boolean;
  error: string | null;
  refreshDocuments: () => Promise<void>;
  deleteDocument: (filename: string) => Promise<void>;
  previewDocument: (filename: string) => Promise<void>;
  downloadDocument: (filename: string) => Promise<void>;
  deleteAllDocuments: () => Promise<void>;
}

/**
 * Hook to manage user documents (list, delete)
 * Now with Firebase Auth token support for secure API calls
 */
export const useDocuments = (userId: string | null): UseDocumentsResult => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { getIdToken } = useAuth();

  const refreshDocuments = useCallback(async () => {
    if (!userId) {
      setDocuments([]);
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      // Get Firebase Auth token
      const token = await getIdToken();
      if (!token) {
        throw new Error("No authentication token available");
      }

      const url = `${API_BASE_URL}/documents/list?user_id=${userId}&_t=${Date.now()}`;

      const response = await fetch(url, {
        cache: "no-store",
        headers: {
          "Cache-Control": "no-cache",
          Authorization: `Bearer ${token}`,
        },
      });
      if (!response.ok) {
        throw new Error(`Failed to fetch documents: ${response.statusText}`);
      }

      const data: DocumentsResponse = await response.json();
      // Ensure we always set an array, even if data.documents is null/undefined
      setDocuments(Array.isArray(data.documents) ? data.documents : []);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : "Unknown error";
      // Only log error if it's not a network/fetch error (server offline)
      if (err instanceof TypeError && errorMsg.includes("fetch")) {
        console.warn("Document service is unavailable.");
      } else {
        console.error("Unable to load documents.");
      }
      setError(errorMsg);
      setDocuments([]);
    } finally {
      setIsLoading(false);
    }
  }, [userId]);

  const deleteDocument = useCallback(
    async (filename: string) => {
      if (!userId) {
        throw new Error("User ID is required");
      }

      // Get Firebase Auth token
      const token = await getIdToken();
      if (!token) {
        throw new Error("No authentication token available");
      }

      const response = await fetch(
        `${API_BASE_URL}/documents/delete?user_id=${userId}&filename=${encodeURIComponent(
          filename
        )}`,
        {
          method: "DELETE",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to delete document: ${response.statusText}`);
      }

      await response.json();

      // Trigger document status refresh
      globalThis.window.dispatchEvent(new Event("refreshDocumentStatus"));

      // Refresh the list
      await refreshDocuments();
    },
    [userId, refreshDocuments]
  );

  const deleteAllDocuments = useCallback(async () => {
    if (!userId) {
      throw new Error("User ID is required");
    }

    // Get Firebase Auth token
    const token = await getIdToken();
    if (!token) {
      throw new Error("No authentication token available");
    }

    const response = await fetch(`${API_BASE_URL}/documents/delete-all?user_id=${userId}`, {
      method: "DELETE",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Failed to delete all documents: ${response.statusText}`);
    }

    await response.json();

    // Trigger document status refresh
    globalThis.window.dispatchEvent(new Event("refreshDocumentStatus"));

    // Refresh the list
    await refreshDocuments();
  }, [userId, refreshDocuments]);

  const getDocumentContent = useCallback(
    async (filename: string, download = false) => {
      try {
        const token = await getIdToken();
        if (!token) {
          return null;
        }
        return await fetchDocumentContent(filename, token, download);
      } catch {
        return null;
      }
    },
    [getIdToken]
  );

  const previewDocument = useCallback(
    async (filename: string) => {
      const file = await getDocumentContent(filename);
      if (!file) return;
      const objectUrl = URL.createObjectURL(file);
      globalThis.window.open(objectUrl, "_blank", "noopener,noreferrer");
    },
    [getDocumentContent]
  );

  const downloadDocument = useCallback(
    async (filename: string) => {
      const file = await getDocumentContent(filename, true);
      if (!file) return;
      const objectUrl = URL.createObjectURL(file);
      const link = document.createElement("a");
      link.href = objectUrl;
      link.download = filename;
      link.click();
      URL.revokeObjectURL(objectUrl);
    },
    [getDocumentContent]
  );

  // Load documents on mount and when userId changes
  useEffect(() => {
    refreshDocuments();
  }, [refreshDocuments]);

  // NOTE: Removed 'documentUploaded' listener to prevent multiple refreshes
  // DocumentManager now handles refresh after upload completion directly

  return {
    documents,
    isLoading,
    error,
    refreshDocuments,
    deleteDocument,
    previewDocument,
    downloadDocument,
    deleteAllDocuments,
  };
};
