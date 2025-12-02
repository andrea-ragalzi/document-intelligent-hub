import { useState } from "react";
import type { Document } from "../DocumentList";

interface UseDocumentSelectionOptions {
  documents: Document[];
}

export const useDocumentSelection = ({ documents }: UseDocumentSelectionOptions) => {
  const [selectedDocs, setSelectedDocs] = useState<string[]>([]);
  const [deleteMultipleModalOpen, setDeleteMultipleModalOpen] = useState(false);

  const isSelectionMode = selectedDocs.length > 0;

  const handleSelect = (filename: string) => {
    setSelectedDocs(prev =>
      prev.includes(filename) ? prev.filter(f => f !== filename) : [...prev, filename]
    );
  };

  const handleSelectAll = () => {
    if (selectedDocs.length === documents.length) {
      setSelectedDocs([]);
    } else {
      setSelectedDocs(documents.map(d => d.filename));
    }
  };

  const handleDeleteSelected = () => {
    if (selectedDocs.length === 0) return;
    setDeleteMultipleModalOpen(true);
  };

  const confirmDeleteSelected = (onDelete: (filename: string) => void) => {
    // Delete all selected documents
    selectedDocs.forEach(filename => {
      onDelete(filename);
    });
    // Reset selection
    setSelectedDocs([]);
    setDeleteMultipleModalOpen(false);
  };

  const closeDeleteMultipleModal = () => {
    setDeleteMultipleModalOpen(false);
  };

  return {
    selectedDocs,
    isSelectionMode,
    deleteMultipleModalOpen,
    handleSelect,
    handleSelectAll,
    handleDeleteSelected,
    confirmDeleteSelected,
    closeDeleteMultipleModal,
  };
};
