import { X, ChevronLeft } from "lucide-react";

interface SidebarHeaderProps {
  activeView: "menu" | "documents" | "settings";
  onClose: () => void;
  onBackToMenu: () => void;
}

export const SidebarHeader: React.FC<SidebarHeaderProps> = ({
  activeView,
  onClose,
  onBackToMenu,
}) => {
  if (activeView === "menu") return null;

  const title = activeView === "documents" ? "Documents" : "Settings";

  return (
    <div className="flex items-center justify-between p-4 border-b border-line/15 gap-2">
      <button
        onClick={onBackToMenu}
        className="flex items-center gap-2 text-base text-muted hover:text-ink transition-all duration-200 ease-in-out h-11 w-11 justify-center rounded-lg hover:bg-surface-hover focus:outline-none focus:ring-3 focus:ring-focus"
      >
        <ChevronLeft size={20} className="text-muted" />
      </button>
      <h2 className="flex-1 text-center text-xl font-semibold text-ink">{title}</h2>
      <button
        onClick={onClose}
        className="h-11 w-11 flex items-center justify-center rounded-lg hover:bg-surface-hover transition-all duration-200 ease-in-out xl:hidden focus:outline-none focus:ring-3 focus:ring-focus"
      >
        <X size={20} className="text-muted" />
      </button>
    </div>
  );
};
