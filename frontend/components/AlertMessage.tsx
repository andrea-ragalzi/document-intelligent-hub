import type { AlertState } from "@/lib/types";
import { CheckCircle, AlertTriangle, Info } from "lucide-react";

interface AlertMessageProps {
  alert: AlertState | null;
}

export const AlertMessage: React.FC<AlertMessageProps> = ({ alert }) => {
  if (!alert?.message) return null;

  let Icon;
  let classes = "";

  switch (alert.type) {
    case "success":
      Icon = CheckCircle;
      classes =
        "bg-green-50 border-green-200 text-green-700 dark:bg-green-900/20 dark:border-green-800 dark:text-green-300";
      break;
    case "error":
      Icon = AlertTriangle;
      classes =
        "bg-red-50 border-red-200 text-red-700 dark:bg-red-900/20 dark:border-red-800 dark:text-red-300";
      break;
    case "info":
    default:
      Icon = Info;
      classes =
        "bg-blue-50 border-blue-200 text-blue-700 dark:bg-blue-900/20 dark:border-blue-800 dark:text-blue-300";
      break;
  }

  return (
    <div
      className={`p-3 rounded-xl flex items-start mt-4 border shadow-sm transition-all duration-300 ${classes}`}
    >
      <Icon size={18} className="flex-shrink-0 mt-0.5 mr-3" />
      <span className="font-medium text-sm leading-snug">{alert.message}</span>
    </div>
  );
};
