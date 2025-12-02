import { FileText, Trash2 } from "lucide-react";
import type { Document } from "@/hooks/useDocuments";
import { formatDate } from "./documentHelpers";

interface IndexedDocumentsListProps {
  documents: Document[];
  deletingDoc: string | null;
  onDeleteClick: (filename: string) => void;
}

export const IndexedDocumentsList: React.FC<IndexedDocumentsListProps> = ({
  documents,
  deletingDoc,
  onDeleteClick,
}) => {
  return (
    <div className="space-y-3 max-h-60 overflow-y-auto pr-2">
      {documents.map(doc => (
        <div
          key={doc.filename}
          className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg shadow-sm hover:shadow-md transition border border-gray-200 dark:border-gray-600"
        >
          <div className="flex items-center space-x-3 min-w-0 flex-1">
            <FileText size={20} className="text-blue-600 flex-shrink-0" />
            <div className="min-w-0 flex-1">
              <p
                className="font-semibold truncate text-gray-900 dark:text-white text-sm"
                title={doc.filename}
              >
                {doc.filename}
              </p>
              <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                <span>{doc.chunks_count?.toLocaleString() || "0"} chunks</span>
                {doc.language && doc.language !== "unknown" && (
                  <>
                    <span>•</span>
                    <span className="uppercase">{doc.language}</span>
                  </>
                )}
                {doc.uploaded_at && (
                  <>
                    <span>•</span>
                    <span>{formatDate(doc.uploaded_at)}</span>
                  </>
                )}
              </div>
            </div>
          </div>
          <button
            onClick={() => onDeleteClick(doc.filename)}
            disabled={deletingDoc === doc.filename}
            className="flex items-center space-x-1 text-red-600 hover:text-red-800 dark:hover:text-red-400 text-xs font-semibold transition px-3 py-1.5 rounded hover:bg-red-50 dark:hover:bg-red-900/20 disabled:opacity-50"
            title="Delete document"
          >
            <Trash2 size={14} />
            <span>{deletingDoc === doc.filename ? "Deleting..." : "Delete"}</span>
          </button>
        </div>
      ))}
    </div>
  );
};
