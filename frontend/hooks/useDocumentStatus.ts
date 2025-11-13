"use client";

import { useState, useEffect } from "react";
import { API_BASE_URL } from "@/lib/constants";

interface DocumentStatus {
  hasDocuments: boolean;
  isChecking: boolean;
  documentCount: number;
}

/**
 * Hook to check if user has uploaded documents
 * Returns document status to enable/disable chat
 */
export const useDocumentStatus = (userId: string | null): DocumentStatus => {
  const [hasDocuments, setHasDocuments] = useState(false);
  const [isChecking, setIsChecking] = useState(true);
  const [documentCount, setDocumentCount] = useState(0);
  const [refreshKey, setRefreshKey] = useState(0);

  // Expose refresh function
  useEffect(() => {
    // Listen for custom event to refresh document status
    const handleRefresh = () => setRefreshKey((prev) => prev + 1);
    window.addEventListener("refreshDocumentStatus", handleRefresh);
    return () =>
      window.removeEventListener("refreshDocumentStatus", handleRefresh);
  }, []);

  useEffect(() => {
    const checkDocuments = async () => {
      if (!userId) {
        setHasDocuments(false);
        setIsChecking(false);
        return;
      }

      setIsChecking(true);
      try {
        // Check if there are indexed documents for this user
        const response = await fetch(
          `${API_BASE_URL}/documents/check?user_id=${userId}`
        );

        if (response.ok) {
          const data = await response.json();
          setHasDocuments(data.has_documents || false);
          setDocumentCount(data.document_count || 0);
        } else {
          setHasDocuments(false);
          setDocumentCount(0);
        }
      } catch (error) {
        console.error("Error checking document status:", error);
        setHasDocuments(false);
        setDocumentCount(0);
      } finally {
        setIsChecking(false);
      }
    };

    checkDocuments();
  }, [userId, refreshKey]); // Re-check when refreshKey changes

  return { hasDocuments, isChecking, documentCount };
};
