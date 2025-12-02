import { useState, useRef, useEffect } from "react";

interface UseDocumentMenuOptions {
  isSelectionMode: boolean;
}

export const useDocumentMenu = ({ isSelectionMode }: UseDocumentMenuOptions) => {
  const [openKebabId, setOpenKebabId] = useState<string | null>(null);
  const [menuPosition, setMenuPosition] = useState<{
    top: number;
    right: number;
  } | null>(null);
  const kebabRef = useRef<{ [key: string]: HTMLDivElement | null }>({});
  const menuRef = useRef<HTMLDivElement | null>(null);

  // Mobile gestures: long-press and drag
  const [longPressTimer, setLongPressTimer] = useState<NodeJS.Timeout | null>(null);
  const [dragY, setDragY] = useState(0);
  const [isDragging, setIsDragging] = useState(false);
  const dragStartY = useRef(0);

  const closeContextMenu = () => {
    setOpenKebabId(null);
    setMenuPosition(null);
    setDragY(0);
    setIsDragging(false);
    menuRef.current = null;
  };

  const runActionAndCloseMenu = (action: () => void | Promise<void>) => {
    try {
      const result = action();
      if (result instanceof Promise) {
        result.catch(error => console.error("Document menu action failed:", error));
      }
    } finally {
      closeContextMenu();
    }
  };

  // Touch handlers for mobile gestures
  const handleTouchStart = (e: React.TouchEvent, filename: string) => {
    if (isSelectionMode) return;

    const target = e.currentTarget;
    const timer = setTimeout(() => {
      if (!target) {
        return;
      }
      const rect = target.getBoundingClientRect();
      setMenuPosition({
        top: rect.bottom + window.scrollY + 8,
        right: window.innerWidth - rect.right + window.scrollX,
      });
      setOpenKebabId(filename);
    }, 200);

    setLongPressTimer(timer);
  };

  const handleTouchEnd = () => {
    if (longPressTimer) {
      clearTimeout(longPressTimer);
      setLongPressTimer(null);
    }
  };

  const handleDragStart = (e: React.TouchEvent) => {
    setIsDragging(true);
    dragStartY.current = e.touches[0].clientY;
  };

  const handleDragMove = (e: React.TouchEvent) => {
    if (!isDragging) return;

    const deltaY = e.touches[0].clientY - dragStartY.current;
    if (deltaY > 0) {
      setDragY(deltaY);
    }
  };

  const handleDragEnd = () => {
    if (dragY > 100) {
      closeContextMenu();
    } else {
      setIsDragging(false);
      setDragY(0);
    }
  };

  // Close kebab menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (!openKebabId) {
        return;
      }

      const kebabElement = kebabRef.current[openKebabId];
      const menuElement = menuRef.current;
      const targetNode = event.target as Node;

      const clickedInsideTrigger = kebabElement?.contains(targetNode);
      const clickedInsideMenu = menuElement?.contains(targetNode);

      if (!clickedInsideTrigger && !clickedInsideMenu) {
        closeContextMenu();
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [openKebabId]);

  return {
    openKebabId,
    menuPosition,
    kebabRef,
    menuRef,
    dragY,
    isDragging,
    closeContextMenu,
    runActionAndCloseMenu,
    handleTouchStart,
    handleTouchEnd,
    handleDragStart,
    handleDragMove,
    handleDragEnd,
    setOpenKebabId,
    setMenuPosition,
  };
};
