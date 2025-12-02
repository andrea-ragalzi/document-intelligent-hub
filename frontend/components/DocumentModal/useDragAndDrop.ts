/**
 * Custom hook for drag-and-drop file upload functionality
 */

import { useState } from "react";
import { isPdfFile, createFileChangeEvent } from "./documentHelpers";

interface UseDragAndDropProps {
  fileInputRef: React.RefObject<HTMLInputElement | null>;
}

export function useDragAndDrop({ fileInputRef }: UseDragAndDropProps) {
  const [dragActive, setDragActive] = useState(false);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      if (isPdfFile(droppedFile)) {
        createFileChangeEvent(droppedFile, fileInputRef);
      }
    }
  };

  return {
    dragActive,
    handleDrag,
    handleDrop,
  };
}
