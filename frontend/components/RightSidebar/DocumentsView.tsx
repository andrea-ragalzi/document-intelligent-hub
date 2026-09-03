import DocumentList from "../DocumentList";
import type { Document } from "../DocumentList";

interface DocumentsViewProps {
  documents: Document[] | undefined;
  onDeleteDocument: (filename: string) => void;
  onPreviewDocument: (filename: string) => Promise<void>;
  onDownloadDocument: (filename: string) => Promise<void>;
  isServerOnline?: boolean;
}

export const DocumentsView: React.FC<DocumentsViewProps> = ({
  documents,
  onDeleteDocument,
  onPreviewDocument,
  onDownloadDocument,
  isServerOnline = true,
}) => {
  return (
    <div className="p-4 flex-1 flex flex-col overflow-hidden">
      <DocumentList
        documents={documents}
        deletingDoc={null}
        onDelete={onDeleteDocument}
        onPreview={onPreviewDocument}
        onDownload={onDownloadDocument}
        isServerOnline={isServerOnline}
      />
    </div>
  );
};
