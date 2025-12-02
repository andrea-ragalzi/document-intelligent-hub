import { Trash2 } from "lucide-react";
import { createPortal } from "react-dom";

interface DocumentContextMenuProps {
  isOpen: boolean;
  menuPosition: { top: number; right: number } | null;
  dragY: number;
  isDragging: boolean;
  selectedDoc: string | null;
  isServerOnline?: boolean;
  menuRef: React.MutableRefObject<HTMLDivElement | null>;
  onClose: () => void;
  onDelete: (filename: string) => void;
  onDragStart: (e: React.TouchEvent) => void;
  onDragMove: (e: React.TouchEvent) => void;
  onDragEnd: () => void;
  runActionAndCloseMenu: (action: () => void) => void;
}

export const DocumentContextMenu: React.FC<DocumentContextMenuProps> = ({
  isOpen,
  menuPosition,
  dragY,
  isDragging,
  selectedDoc,
  isServerOnline = true,
  menuRef,
  onClose,
  onDelete,
  onDragStart,
  onDragMove,
  onDragEnd,
  runActionAndCloseMenu,
}) => {
  if (!isOpen || !menuPosition || !selectedDoc) return null;

  return createPortal(
    <>
      {/* Backdrop for mobile */}
      <div
        aria-hidden="true"
        className="fixed inset-0 bg-black/70 dark:bg-indigo-950/90 z-[100] md:hidden"
        onClick={e => {
          e.stopPropagation();
          onClose();
        }}
        onKeyDown={e => e.key === "Escape" && onClose()}
      />
      {/* Menu - Mobile: draggable bottom sheet, Desktop: positioned dropdown */}
      <div
        className="fixed inset-x-0 md:inset-x-auto md:bottom-auto bg-gradient-to-b from-indigo-900 to-indigo-950 dark:from-slate-900 dark:to-black rounded-t-3xl md:rounded-lg shadow-2xl border-0 z-[110] transition-transform overflow-hidden"
        ref={node => {
          menuRef.current = node;
        }}
        style={{
          bottom: window.innerWidth < 768 ? `${-dragY}px` : undefined,
          height: window.innerWidth < 768 ? "35vh" : undefined,
          top: window.innerWidth >= 768 ? `${menuPosition.top}px` : undefined,
          right: window.innerWidth >= 768 ? `${menuPosition.right}px` : undefined,
          width: window.innerWidth >= 768 ? "200px" : undefined,
        }}
        onTouchStart={onDragStart}
        onTouchMove={onDragMove}
        onTouchEnd={onDragEnd}
        onClick={e => e.stopPropagation()}
      >
        {/* Drag Handle - Mobile only */}
        <div className="md:hidden flex justify-center py-2 border-b border-indigo-700 dark:border-slate-700">
          <div
            className={`w-12 h-1.5 rounded-full transition-all duration-200 ${
              isDragging ? "bg-indigo-400" : "bg-indigo-600 dark:bg-slate-600"
            }`}
          />
        </div>

        {/* Menu Items */}
        <div className="p-2">
          <button
            onClick={() => runActionAndCloseMenu(() => onDelete(selectedDoc))}
            disabled={isServerOnline === false}
            className="w-full text-left px-4 py-3 rounded-lg text-red-300 hover:bg-red-900/30 transition-colors flex items-center gap-3 disabled:opacity-50 disabled:cursor-not-allowed"
            title={
              isServerOnline === false ? "Server offline - delete unavailable" : "Delete document"
            }
          >
            <Trash2 size={18} />
            <span className="font-medium">Delete</span>
          </button>
        </div>
      </div>
    </>,
    document.body
  );
};
