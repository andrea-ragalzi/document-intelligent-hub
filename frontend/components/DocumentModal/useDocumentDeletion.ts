/**
 * Custom hook for document deletion functionality
 */

import { useState } from "react";

interface UseDocumentDeletionProps {
  deleteDocument: (filename: string) => Promise<void>;
}

export function useDocumentDeletion({ deleteDocument }: UseDocumentDeletionProps) {
  const [deletingDoc, setDeletingDoc] = useState<string | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<string | null>(null);

  const handleDelete = async (filename: string) => {
    setDeletingDoc(filename);
    try {
      await deleteDocument(filename);
      setShowDeleteConfirm(null);
    } catch (error) {
      console.error("Error deleting document:", error);
    } finally {
      setDeletingDoc(null);
    }
  };

  const openDeleteConfirm = (filename: string) => {
    setShowDeleteConfirm(filename);
  };

  const closeDeleteConfirm = () => {
    setShowDeleteConfirm(null);
  };

  return {
    deletingDoc,
    showDeleteConfirm,
    handleDelete,
    openDeleteConfirm,
    closeDeleteConfirm,
  };
}
