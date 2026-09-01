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
    <div className="flex items-center justify-between p-6 border-b border-line/15">
      <div className="flex items-center gap-3">
        <div className="p-2 bg-red-100 dark:bg-red-900/30 rounded-lg">
          <Bug size={24} className="text-red-600 dark:text-red-400" />
        </div>
        <h2 className="text-xl font-semibold text-ink">Report a Bug</h2>
      </div>
      <button
        onClick={onClose}
        disabled={isSubmitting}
        className="p-2 hover:bg-surface-hover rounded-lg transition-colors disabled:opacity-50"
      >
        <X size={24} className="text-muted" />
      </button>
    </div>
  );
};
