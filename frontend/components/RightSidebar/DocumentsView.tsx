import DocumentList from "../DocumentList";
import type { Document } from "../DocumentList";

interface DocumentsViewProps {
  documents: Document[] | undefined;
  onDeleteDocument: (filename: string) => void;
  isServerOnline?: boolean;
}

export const DocumentsView: React.FC<DocumentsViewProps> = ({
  documents,
  onDeleteDocument,
  isServerOnline = true,
}) => {
  return (
    <div className="p-4 flex-1 flex flex-col overflow-hidden">
      <DocumentList
        documents={documents}
        deletingDoc={null}
        onDelete={onDeleteDocument}
        isServerOnline={isServerOnline}
      />
    </div>
  );
};
