import { FormEvent } from "react";
import { Save, X, AlertCircle } from "lucide-react";

interface SaveModalProps {
  isOpen: boolean;
  conversationName: string;
  setConversationName: (name: string) => void;
  onClose: () => void;
  onSave: (e: FormEvent) => void;
  errorMessage?: string;
}

export const SaveModal: React.FC<SaveModalProps> = ({
  isOpen,
  conversationName,
  setConversationName,
  onClose,
  onSave,
  errorMessage,
}) => {
  console.log("📋 SaveModal render - isOpen:", isOpen);

  if (!isOpen) return null;

  console.log("✅ SaveModal is rendering!");

  return (
    <div className="fixed inset-0 bg-gray-900 bg-opacity-50 dark:bg-opacity-70 z-[60] flex items-center justify-center p-4">
      <form
        onSubmit={onSave}
        className="bg-white dark:bg-gray-800 rounded-xl p-6 w-full max-w-sm shadow-2xl"
      >
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-xl font-bold text-gray-900 dark:text-white flex items-center">
            <Save size={20} className="mr-2 text-blue-600" /> Salva Chat
          </h3>
          <button
            type="button"
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            <X size={20} />
          </button>
        </div>
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
          Assegna un nome per salvare la conversazione.
        </p>

        {errorMessage && (
          <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg flex items-start">
            <AlertCircle
              size={18}
              className="text-red-600 dark:text-red-400 mr-2 flex-shrink-0 mt-0.5"
            />
            <p className="text-sm text-red-600 dark:text-red-400">
              {errorMessage}
            </p>
          </div>
        )}

        <input
          type="text"
          value={conversationName}
          onChange={(e) => setConversationName(e.target.value)}
          placeholder="Nome della conversazione (es. Report Q3)"
          className="w-full p-3 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500 shadow-inner dark:bg-gray-900 dark:border-gray-600 dark:text-white text-sm"
          required
        />
        <button
          type="submit"
          className="mt-4 w-full flex justify-center items-center py-3 px-4 text-sm font-bold rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition duration-200 shadow-md"
        >
          <Save size={18} className="mr-2" />
          Salva
        </button>
      </form>
    </div>
  );
};
