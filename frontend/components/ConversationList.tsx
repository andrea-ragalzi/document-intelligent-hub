import type { SavedConversation } from "@/lib/types";
import { BookOpen, Trash2, Archive, Edit } from "lucide-react";

interface ConversationListProps {
  conversations: SavedConversation[];
  onLoad: (conv: SavedConversation) => void;
  onDelete: (id: string, name: string) => void;
  onRename: (id: string, currentName: string) => void;
}

export const ConversationList: React.FC<ConversationListProps> = ({
  conversations,
  onLoad,
  onDelete,
  onRename,
}) => {
  return (
    <section className="pt-4">
      <h2 className="text-lg font-bold text-gray-800 dark:text-white mb-3 flex items-center border-b border-gray-100 dark:border-gray-700 pb-2">
        <Archive size={16} className="mr-2 text-blue-600" /> 2. Conversazioni
        Salvate
      </h2>
      <div className="space-y-2 max-h-64 overflow-y-auto pr-2">
        {conversations.length === 0 ? (
          <p className="text-sm text-gray-500 dark:text-gray-400 italic">
            Nessuna conversazione salvata.
          </p>
        ) : (
          conversations.map((conv) => (
            <div
              key={conv.id}
              className="flex items-center justify-between p-3 border border-gray-200 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-700/50 hover:bg-gray-100 dark:hover:bg-gray-700 transition duration-150"
            >
              <div className="flex-1 min-w-0">
                <p className="font-semibold text-sm text-gray-800 dark:text-white truncate">
                  {conv.name}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                  {conv.timestamp}
                </p>
              </div>
              <div className="flex space-x-1 ml-4 flex-shrink-0">
                <button
                  onClick={() => onLoad(conv)}
                  title="Carica conversazione"
                  className="p-1.5 rounded-full text-blue-600 hover:bg-blue-100 dark:hover:bg-gray-600 transition"
                >
                  <BookOpen size={16} />
                </button>
                <button
                  onClick={() => onRename(conv.id, conv.name)}
                  title="Rinomina conversazione"
                  className="p-1.5 rounded-full text-green-600 hover:bg-green-100 dark:hover:bg-gray-600 transition"
                >
                  <Edit size={16} />
                </button>
                <button
                  onClick={() => onDelete(conv.id, conv.name)}
                  title="Elimina conversazione"
                  className="p-1.5 rounded-full text-red-600 hover:bg-red-100 dark:hover:bg-gray-600 transition"
                >
                  <Trash2 size={16} />
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </section>
  );
};
