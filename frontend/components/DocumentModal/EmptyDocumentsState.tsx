import { AlertCircle } from "lucide-react";

export const EmptyDocumentsState: React.FC = () => {
  return (
    <div className="text-center py-8 px-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
      <AlertCircle size={40} className="mx-auto text-gray-400 mb-3" />
      <p className="text-gray-500 dark:text-gray-400 italic">No documents uploaded yet.</p>
      <p className="text-sm text-gray-400 dark:text-gray-500 mt-1">
        Upload a PDF to start asking questions.
      </p>
    </div>
  );
};
