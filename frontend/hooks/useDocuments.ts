"use client";

import { useState, useEffect, useCallback } from "react";
import { API_BASE_URL } from "@/lib/constants";
import { useAuth } from "@/contexts/AuthContext";

export interface Document {
  filename: string;
  chunks_count: number;
  language?: string;
  uploaded_at?: string;
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
      console.log("⚠️ No userId, skipping document refresh");
      setDocuments([]);
      setIsLoading(false);
      return;
    }

    const timestamp = new Date().toISOString();
    console.log(`🔄 [${timestamp}] Refreshing documents for user:`, userId);
    setIsLoading(true);
    setError(null);

    try {
      // Get Firebase Auth token
      const token = await getIdToken();
      if (!token) {
        throw new Error("No authentication token available");
      }

      const url = `${API_BASE_URL}/documents/list?user_id=${userId}&_t=${Date.now()}`;
      console.log("📡 Fetching:", url);

      const response = await fetch(url, {
        cache: "no-store",
        headers: {
          "Cache-Control": "no-cache",
          Authorization: `Bearer ${token}`,
        },
      });
      console.log("📨 Response received, status:", response.status);

      if (!response.ok) {
        console.error("❌ Response not OK:", response.status, response.statusText);
        throw new Error(`Failed to fetch documents: ${response.statusText}`);
      }

      console.log("⏳ Parsing JSON...");
      const data: DocumentsResponse = await response.json();
      console.log(
        `📄 [${timestamp}] Documents loaded:`,
        data.documents.length,
        "documents:",
        data.documents.map(d => d.filename)
      );
      console.log("💾 Setting documents state...");
      // Ensure we always set an array, even if data.documents is null/undefined
      setDocuments(Array.isArray(data.documents) ? data.documents : []);
      console.log("✅ Documents state updated successfully");
      console.log("🔍 Current documents in state:", data.documents?.length || 0);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : "Unknown error";
      // Only log error if it's not a network/fetch error (server offline)
      if (err instanceof TypeError && errorMsg.includes("fetch")) {
        console.log("⚠️ Server offline - documents unavailable");
      } else {
        console.error("❌ Error loading documents:", errorMsg);
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

      console.log("🗑️ Deleting document:", filename);

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

      const result = await response.json();
      console.log("✅ Document deleted:", result);

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

    console.log("🗑️ Deleting all documents for user:", userId);

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

    const result = await response.json();
    console.log("✅ All documents deleted:", result);

    // Trigger document status refresh
    globalThis.window.dispatchEvent(new Event("refreshDocumentStatus"));

    // Refresh the list
    await refreshDocuments();
  }, [userId, refreshDocuments]);

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
    deleteAllDocuments,
  };
};
