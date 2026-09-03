import { Download, Eye, Trash2 } from "lucide-react";
import { createPortal } from "react-dom";

interface DocumentContextMenuProps {
  isOpen: boolean;
  menuPosition: { top: number; right: number } | null;
  dragY: number;
  isDragging: boolean;
  selectedDoc: string | null;
  originalAvailable: boolean;
  isServerOnline?: boolean;
  menuRef: React.MutableRefObject<HTMLDivElement | null>;
  onClose: () => void;
  onDelete: (filename: string) => void;
  onPreview: (filename: string) => Promise<void>;
  onDownload: (filename: string) => Promise<void>;
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
  originalAvailable,
  isServerOnline = true,
  menuRef,
  onClose,
  onDelete,
  onPreview,
  onDownload,
  onDragStart,
  onDragMove,
  onDragEnd,
  runActionAndCloseMenu,
}) => {
  if (!isOpen || !menuPosition || !selectedDoc) return null;
  const documentActionsDisabled = isServerOnline === false || !originalAvailable;

  return createPortal(
    <>
      {/* Backdrop for mobile */}
      <div
        aria-hidden="true"
        className="fixed inset-0 bg-black/70 z-[100] md:hidden"
        onClick={e => {
          e.stopPropagation();
          onClose();
        }}
        onKeyDown={e => e.key === "Escape" && onClose()}
      />
      {/* Menu - Mobile: draggable bottom sheet, Desktop: positioned dropdown */}
      <div
        className="fixed inset-x-0 md:inset-x-auto md:bottom-auto bg-surface rounded-t-3xl md:rounded-lg shadow-xl border border-line/15 z-[110] transition-transform overflow-hidden"
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
      >
        {/* Drag Handle - Mobile only */}
        <div className="md:hidden flex justify-center py-2 border-b border-line/15">
          <div
            className={`w-12 h-1.5 rounded-full transition-all duration-200 ${
              isDragging ? "bg-accent/60" : "bg-muted"
            }`}
          />
        </div>

        {/* Menu Items */}
        <div className="p-2">
          <button
            onClick={() => runActionAndCloseMenu(() => onPreview(selectedDoc))}
            disabled={documentActionsDisabled}
            className="w-full text-left px-4 py-3 rounded-lg text-ink hover:bg-surface-hover transition-colors flex items-center gap-3 disabled:opacity-50 disabled:cursor-not-allowed"
            aria-label="Preview document"
            title="Preview document"
          >
            <Eye size={18} />
            <span className="font-medium">Preview</span>
          </button>
          <button
            onClick={() => runActionAndCloseMenu(() => onDownload(selectedDoc))}
            disabled={documentActionsDisabled}
            className="w-full text-left px-4 py-3 rounded-lg text-ink hover:bg-surface-hover transition-colors flex items-center gap-3 disabled:opacity-50 disabled:cursor-not-allowed"
            aria-label="Download document"
            title="Download document"
          >
            <Download size={18} />
            <span className="font-medium">Download</span>
          </button>
          <button
            onClick={() => runActionAndCloseMenu(() => onDelete(selectedDoc))}
            disabled={isServerOnline === false}
            className="w-full text-left px-4 py-3 rounded-lg text-red-300 hover:bg-red-900/30 transition-colors flex items-center gap-3 disabled:opacity-50 disabled:cursor-not-allowed"
            title={
              isServerOnline === false ? "Server offline - delete unavailable" : "Delete document"
            }
            aria-label="Delete document"
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
