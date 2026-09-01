import { FileText, MoreVertical, CheckCircle } from "lucide-react";
import type { Document } from "../DocumentList";

interface DocumentItemProps {
  doc: Document;
  isSelected: boolean;
  isSelectionMode: boolean;
  isKebabOpen: boolean;
  onSelect: (filename: string) => void;
  onTouchStart: (e: React.TouchEvent, filename: string) => void;
  onTouchEnd: () => void;
  onContextMenu: (e: React.MouseEvent, rect: DOMRect) => void;
  onKebabClick: (e: React.MouseEvent, rect: DOMRect) => void;
  onCloseKebab: () => void;
  kebabRef: (el: HTMLDivElement | null, filename: string) => void;
}

export const DocumentItem: React.FC<DocumentItemProps> = ({
  doc,
  isSelected,
  isSelectionMode,
  isKebabOpen,
  onSelect,
  onTouchStart,
  onTouchEnd,
  onContextMenu,
  onKebabClick,
  onCloseKebab,
  kebabRef,
}) => {
  return (
    <div
      key={doc.filename}
      role="button"
      tabIndex={0}
      aria-label={`Document: ${doc.filename}`}
      className={`group relative w-full text-left rounded-lg p-3 transform hover:scale-[1.01] transition-all duration-200 ease-in-out hover:shadow-sm ${
        isSelected
          ? "bg-accent/15 border border-accent"
          : "bg-surface border border-line/15 hover:bg-surface-hover hover:border-line/30"
      } cursor-pointer`}
      onClick={() => {
        if (isSelectionMode) {
          onSelect(doc.filename);
        }
      }}
      onKeyDown={e => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          if (isSelectionMode) {
            onSelect(doc.filename);
          }
        }
      }}
      onTouchStart={e => onTouchStart(e, doc.filename)}
      onTouchEnd={onTouchEnd}
      onContextMenu={e => {
        if (!isSelectionMode) {
          e.preventDefault();
          const rect = e.currentTarget.getBoundingClientRect();
          onContextMenu(e, rect);
        }
      }}
    >
      <div className="flex items-center gap-3">
        {/* Selection indicator - Only for selected items */}
        {isSelected && (
          <div className="flex-shrink-0 h-6 w-6 flex items-center justify-center rounded-full bg-accent">
            <CheckCircle size={16} className="text-on-accent" />
          </div>
        )}

        {/* Document icon - Always visible when not selected */}
        {!isSelected && (
          <div className="flex-shrink-0 w-6 h-6 bg-raised rounded flex items-center justify-center">
            <FileText size={14} className="text-accent" />
          </div>
        )}

        {/* Document content */}
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-gray-900 dark:text-gray-100 truncate">
            {doc.filename}
          </p>
          <div className="flex items-center gap-2 mt-0.5">
            <span className="text-xs text-gray-500 dark:text-gray-400">
              {doc.chunks_count} chunks
            </span>
            {doc.language && doc.language !== "unknown" && (
              <>
                <span className="text-xs text-gray-400">•</span>
                <span className="text-xs text-gray-500 dark:text-gray-400 uppercase">
                  {doc.language}
                </span>
              </>
            )}
          </div>
        </div>

        {/* Unified container: Kebab menu (hover on desktop) */}
        {!isSelectionMode && (
          <div className="relative flex-shrink-0 h-7 w-7" ref={el => kebabRef(el, doc.filename)}>
            {/* Kebab menu - Visible on mobile tap, visible on hover on desktop */}
            <button
              onClick={e => {
                e.stopPropagation();
                if (isKebabOpen) {
                  onCloseKebab();
                } else {
                  const rect = e.currentTarget.getBoundingClientRect();
                  onKebabClick(e, rect);
                }
              }}
              className="h-full w-full flex items-center justify-center hover:bg-gray-100 dark:hover:bg-gray-600 rounded transition-colors"
              aria-label="Document options"
            >
              <MoreVertical size={16} className="text-gray-600 dark:text-gray-300" />
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
