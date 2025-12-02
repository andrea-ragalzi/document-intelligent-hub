import { Bug, X } from "lucide-react";

interface BugReportModalHeaderProps {
  isSubmitting: boolean;
  onClose: () => void;
}

export const BugReportModalHeader: React.FC<BugReportModalHeaderProps> = ({
  isSubmitting,
  onClose,
}) => {
  return (
    <div className="flex items-center justify-between p-6 border-b-2 border-indigo-100 dark:border-indigo-800">
      <div className="flex items-center gap-3">
        <div className="p-2 bg-red-100 dark:bg-red-900/30 rounded-lg">
          <Bug size={24} className="text-red-600 dark:text-red-400" />
        </div>
        <h2 className="text-xl font-semibold text-indigo-900 dark:text-indigo-50">Report a Bug</h2>
      </div>
      <button
        onClick={onClose}
        disabled={isSubmitting}
        className="p-2 hover:bg-indigo-100 dark:hover:bg-indigo-800 rounded-lg transition-colors disabled:opacity-50"
      >
        <X size={24} className="text-indigo-700 dark:text-indigo-200" />
      </button>
    </div>
  );
};
