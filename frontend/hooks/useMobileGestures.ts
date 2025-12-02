/**
 * useMobileGestures Hook
 *
 * Handles mobile-specific interactions for list items:
 * - Long-press to open context menu
 * - Drag-to-dismiss gesture for mobile action sheets
 * - Desktop kebab menu positioning
 *
 * Eliminates ~100 lines of duplicate code between ConversationList and DocumentList.
 *
 * @template T - The item type (must have an 'id' property)
 */

import { useEffect, useRef, useState } from "react";

export interface UseMobileGesturesOptions {
  /**
   * Long press duration in milliseconds
   * @default 200
   */
  longPressDuration?: number;

  /**
   * Drag distance threshold (px) to trigger dismiss
   * @default 100
   */
  dismissThreshold?: number;

  /**
   * Whether selection mode is active (disables long-press)
   * @default false
   */
  isSelectionMode?: boolean;
}

export interface UseMobileGesturesReturn {
  /** ID of currently open item menu */
  openItemId: string | null;

  /** Menu position for desktop (absolute positioning) */
  menuPosition: { top: number; right: number } | null;

  /** Current drag Y offset for mobile sheet */
  dragY: number;

  /** Whether user is currently dragging */
  isDragging: boolean;

  /** Refs for kebab buttons (desktop) */
  kebabRef: React.RefObject<{ [key: string]: HTMLDivElement | null }>;

  /** Ref for menu container (for click-outside detection) */
  menuRef: React.RefObject<HTMLDivElement | null>;

  /** Close context menu/sheet */
  closeContextMenu: () => void;

  /** Execute action and automatically close menu */
  runActionAndCloseMenu: (action: () => void | Promise<void>) => void;

  /** Handle touch start (long-press detection) */
  handleTouchStart: (e: React.TouchEvent, itemId: string) => void;

  /** Handle touch end (cancel long-press) */
  handleTouchEnd: () => void;

  /** Handle drag start (mobile sheet) */
  handleDragStart: (e: React.TouchEvent) => void;

  /** Handle drag move (mobile sheet) */
  handleDragMove: (e: React.TouchEvent) => void;

  /** Handle drag end (mobile sheet dismiss or snap back) */
  handleDragEnd: () => void;

  /** Handle kebab click (desktop) */
  handleKebabClick: (e: React.MouseEvent, itemId: string) => void;
}

export function useMobileGestures({
  longPressDuration = 200,
  dismissThreshold = 100,
  isSelectionMode = false,
}: UseMobileGesturesOptions = {}): UseMobileGesturesReturn {
  // Desktop kebab menu state
  const [openItemId, setOpenItemId] = useState<string | null>(null);
  const [menuPosition, setMenuPosition] = useState<{
    top: number;
    right: number;
  } | null>(null);
  const kebabRef = useRef<{ [key: string]: HTMLDivElement | null }>({});
  const menuRef = useRef<HTMLDivElement | null>(null);

  // Long press tracking for mobile
  const [longPressTimer, setLongPressTimer] = useState<NodeJS.Timeout | null>(null);

  // Drag state for mobile menu
  const [dragY, setDragY] = useState(0);
  const [isDragging, setIsDragging] = useState(false);
  const dragStartY = useRef(0);

  const closeContextMenu = () => {
    setOpenItemId(null);
    setMenuPosition(null);
    setDragY(0);
    setIsDragging(false);
    menuRef.current = null;
  };

  const runActionAndCloseMenu = (action: () => void | Promise<void>) => {
    try {
      const result = action();
      if (result instanceof Promise) {
        result.catch(error => console.error("Context menu action failed:", error));
      }
    } finally {
      closeContextMenu();
    }
  };

  // Close kebab menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (!openItemId) return;

      const kebabElement = kebabRef.current[openItemId];
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
  }, [openItemId]);

  // Long press handlers for mobile
  const handleTouchStart = (e: React.TouchEvent, itemId: string) => {
    if (isSelectionMode) return;

    const target = e.currentTarget;
    const timer = setTimeout(() => {
      if (!target) return;

      // Open menu on long press
      const rect = target.getBoundingClientRect();
      setMenuPosition({
        top: rect.bottom + window.scrollY + 4,
        right: window.innerWidth - rect.right + window.scrollX,
      });
      setOpenItemId(itemId);
    }, longPressDuration);

    setLongPressTimer(timer);
  };

  const handleTouchEnd = () => {
    if (longPressTimer) {
      clearTimeout(longPressTimer);
      setLongPressTimer(null);
    }
  };

  // Drag handlers for mobile menu
  const handleDragStart = (e: React.TouchEvent) => {
    setIsDragging(true);
    dragStartY.current = e.touches[0].clientY;
  };

  const handleDragMove = (e: React.TouchEvent) => {
    if (!isDragging) return;

    const currentY = e.touches[0].clientY;
    const diff = currentY - dragStartY.current;

    // Only allow downward drag (positive diff)
    if (diff > 0) {
      setDragY(diff);
    }
  };

  const handleDragEnd = () => {
    if (!isDragging) return;

    setIsDragging(false);

    // If dragged beyond threshold, close menu
    if (dragY > dismissThreshold) {
      closeContextMenu();
    } else {
      // Snap back
      setDragY(0);
    }
  };

  // Desktop kebab click handler
  const handleKebabClick = (e: React.MouseEvent, itemId: string) => {
    e.stopPropagation();

    // If same kebab, close it
    if (openItemId === itemId) {
      closeContextMenu();
      return;
    }

    // Get kebab button position
    const kebabElement = kebabRef.current[itemId];
    if (!kebabElement) return;

    const rect = kebabElement.getBoundingClientRect();

    // Position menu below kebab button, aligned to right edge
    setMenuPosition({
      top: rect.bottom + window.scrollY + 4,
      right: window.innerWidth - rect.right + window.scrollX,
    });

    setOpenItemId(itemId);
  };

  return {
    openItemId,
    menuPosition,
    dragY,
    isDragging,
    kebabRef,
    menuRef,
    closeContextMenu,
    runActionAndCloseMenu,
    handleTouchStart,
    handleTouchEnd,
    handleDragStart,
    handleDragMove,
    handleDragEnd,
    handleKebabClick,
  };
}
