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
    <div className="flex items-center justify-between p-4 border-b-2 border-indigo-100 dark:border-indigo-800 gap-2">
      <button
        onClick={onBackToMenu}
        className="flex items-center gap-2 text-base text-indigo-700 dark:text-indigo-200 hover:text-indigo-900 dark:hover:text-indigo-100 transition-all duration-200 ease-in-out h-11 w-11 justify-center rounded-lg hover:bg-indigo-100 dark:hover:bg-indigo-800 focus:outline-none focus:ring-3 focus:ring-focus"
      >
        <ChevronLeft size={20} className="text-indigo-700 dark:text-indigo-200" />
      </button>
      <h2 className="flex-1 text-center text-xl font-bold text-indigo-900 dark:text-indigo-50">
        {title}
      </h2>
      <button
        onClick={onClose}
        className="h-11 w-11 flex items-center justify-center rounded-lg hover:bg-indigo-100 dark:hover:bg-indigo-800 transition-all duration-200 ease-in-out xl:hidden focus:outline-none focus:ring-3 focus:ring-focus"
      >
        <X size={20} className="text-indigo-700 dark:text-indigo-200" />
      </button>
    </div>
  );
};
