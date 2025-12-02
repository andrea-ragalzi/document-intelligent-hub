import { FormEvent, useState } from "react";
import { Edit, X, AlertCircle } from "lucide-react";

interface RenameModalProps {
  isOpen: boolean;
  currentName: string;
  onClose: () => void;
  onRename: (newName: string) => Promise<boolean>;
}

export const RenameModal: React.FC<RenameModalProps> = ({
  isOpen,
  currentName,
  onClose,
  onRename,
}) => {
  const [newName, setNewName] = useState(currentName);
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");

    if (!newName.trim()) {
      setError("Enter a valid name.");
      return;
    }

    if (newName.trim() === currentName) {
      setError("Name is the same as current.");
      return;
    }

    setIsSubmitting(true);
    const success = await onRename(newName.trim());
    setIsSubmitting(false);

    if (success) {
      onClose();
      setNewName("");
    } else {
      setError("Error renaming conversation.");
    }
  };

  const handleClose = () => {
    setNewName(currentName);
    setError("");
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 dark:bg-black/70 z-[60] flex items-center justify-center p-4 font-[Inter]">
      <form
        onSubmit={handleSubmit}
        className="bg-white dark:bg-gray-900 rounded-xl p-6 w-full max-w-sm shadow-xl border border-gray-200 dark:border-gray-700"
      >
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-xl font-bold text-gray-900 dark:text-white flex items-center">
            <Edit size={20} className="mr-2 text-indigo-600" /> Rename Conversation
          </h3>
          <button
            type="button"
            onClick={handleClose}
            className="h-10 w-10 flex items-center justify-center rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        <p className="text-base text-gray-600 dark:text-gray-400 mb-4">
          Current name: <span className="font-semibold">{currentName}</span>
        </p>

        {error && (
          <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-700 rounded-lg flex items-start">
            <AlertCircle
              size={18}
              className="text-red-600 dark:text-red-400 mr-2 flex-shrink-0 mt-0.5"
            />
            <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
          </div>
        )}

        <input
          type="text"
          value={newName}
          onChange={e => setNewName(e.target.value)}
          placeholder="New conversation name"
          className="w-full p-3 text-base border border-gray-300 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 shadow-inner bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 transition-colors"
          required
          autoFocus
        />
        <button
          type="submit"
          disabled={isSubmitting}
          className="mt-4 w-full flex justify-center items-center py-3 px-4 text-base font-semibold rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 disabled:bg-gray-400 dark:disabled:bg-gray-600 disabled:cursor-not-allowed transition-colors shadow-md"
        >
          {isSubmitting ? (
            <>Saving...</>
          ) : (
            <>
              <Edit size={18} className="mr-2" />
              Rename
            </>
          )}
        </button>
      </form>
    </div>
  );
};
