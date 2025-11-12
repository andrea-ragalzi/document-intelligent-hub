import { FileText } from "lucide-react";
import { UploadSection } from "./UploadSection";
import { ConversationList } from "./ConversationList";
import type { SavedConversation, AlertState } from "@/lib/types";
import { FormEvent, ChangeEvent } from "react";

interface SidebarProps {
  userId: string | null;
  file: File | null;
  isUploading: boolean;
  uploadAlert: AlertState;
  statusAlert: AlertState | null;
  savedConversations: SavedConversation[];
  onFileChange: (e: ChangeEvent<HTMLInputElement>) => void;
  onUpload: (e: FormEvent) => void;
  onLoadConversation: (conv: SavedConversation) => void;
  onDeleteConversation: (id: string, name: string) => void;
  onRenameConversation: (id: string, currentName: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  userId,
  file,
  isUploading,
  uploadAlert,
  statusAlert,
  savedConversations,
  onFileChange,
  onUpload,
  onLoadConversation,
  onDeleteConversation,
  onRenameConversation,
}) => {
  return (
    <div className="lg:w-1/3 p-6 bg-white dark:bg-gray-800 rounded-2xl shadow-xl h-full lg:sticky lg:top-6 self-start space-y-6 transition-colors duration-500">
      <div>
        <h1 className="text-3xl font-extrabold text-gray-900 dark:text-white mb-2 flex items-center">
          <FileText className="mr-3 text-blue-600" size={28} />
          Document RAG
        </h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mb-4 flex items-center">
          User ID (Tenant):
          <span
            className={`font-mono font-medium ml-2 px-2 py-0.5 rounded-md text-xs ${
              userId
                ? "bg-blue-100 text-blue-700 dark:bg-blue-900/50 dark:text-blue-300"
                : "bg-yellow-100 text-yellow-700"
            }`}
          >
            {userId ? userId : "Not available"}
          </span>
        </p>
      </div>

      <UploadSection
        file={file}
        isUploading={isUploading}
        userId={userId}
        uploadAlert={uploadAlert}
        statusAlert={statusAlert}
        onFileChange={onFileChange}
        onUpload={onUpload}
      />

      <ConversationList
        conversations={savedConversations}
        onLoad={onLoadConversation}
        onDelete={onDeleteConversation}
        onRename={onRenameConversation}
      />
    </div>
  );
};
