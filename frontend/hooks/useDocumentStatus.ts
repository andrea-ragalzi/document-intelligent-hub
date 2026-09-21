"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { API_BASE_URL } from "@/lib/constants";
import { useAuth } from "@/contexts/AuthContext";

interface DocumentStatus {
  hasDocuments: boolean;
  isChecking: boolean;
  documentCount: number;
  refreshDocumentStatus: () => Promise<boolean>;
}

/**
 * Hook to check if user has uploaded documents
 * Returns document status to enable/disable chat
 */
export const useDocumentStatus = (userId: string | null): DocumentStatus => {
  const [hasDocuments, setHasDocuments] = useState(false);
  const [isChecking, setIsChecking] = useState(true);
  const [documentCount, setDocumentCount] = useState(0);
  const requestSequence = useRef(0);
  const { getIdToken } = useAuth();

  const refreshDocumentStatus = useCallback(async (): Promise<boolean> => {
    const requestId = ++requestSequence.current;
    const isCurrentRequest = () => requestId === requestSequence.current;

    if (!userId) {
      if (isCurrentRequest()) {
        setHasDocuments(false);
        setDocumentCount(0);
        setIsChecking(false);
      }
      return true;
    }

    if (isCurrentRequest()) setIsChecking(true);

    try {
      // Get authentication token
      const token = await getIdToken();
      if (!token) {
        throw new Error("No authentication token available");
      }

      // Check if there are indexed documents for this user
      const response = await fetch(`${API_BASE_URL}/documents/check?user_id=${userId}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!isCurrentRequest()) return false;

      if (response.ok) {
        const data = await response.json();
        if (!isCurrentRequest()) return false;
        setHasDocuments(data.has_documents || false);
        setDocumentCount(data.document_count || 0);
        return true;
      } else {
        console.warn("Document status check failed.");
        return false;
      }
    } catch (error) {
      // Silently handle network errors (server offline)
      if (error instanceof TypeError && error.message.includes("fetch")) {
        console.warn("Document status service is unavailable.");
      } else {
        console.error("Unable to check document status.");
      }
      return false;
    } finally {
      if (isCurrentRequest()) setIsChecking(false);
    }
  }, [getIdToken, userId]);

  useEffect(() => {
    void refreshDocumentStatus();
  }, [refreshDocumentStatus]);

  useEffect(() => {
    const handleRefresh = () => void refreshDocumentStatus();
    globalThis.window.addEventListener("refreshDocumentStatus", handleRefresh);
    return () => globalThis.window.removeEventListener("refreshDocumentStatus", handleRefresh);
  }, [refreshDocumentStatus]);

  return { hasDocuments, isChecking, documentCount, refreshDocumentStatus };
};
