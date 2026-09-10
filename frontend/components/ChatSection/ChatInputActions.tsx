import { Paperclip, Loader, CornerDownLeft } from "lucide-react";

interface ChatInputActionsProps {
  userId: string | null;
  isServerOnline?: boolean;
  isQuerying: boolean;
  query: string;
  isChatDisabled: boolean;
  onOpenUploadModal: () => void;
}

export const ChatInputActions: React.FC<ChatInputActionsProps> = ({
  userId,
  isServerOnline,
  isQuerying,
  query,
  isChatDisabled,
  onOpenUploadModal,
}) => {
  return (
    <div className="flex items-center justify-between px-4 pb-4 sm:pb-4">
      {/* Left Action Buttons */}
      <div className="flex items-center gap-1">
        {/* Upload Button */}
        <button
          type="button"
          onClick={onOpenUploadModal}
          disabled={!userId || !isServerOnline}
          className="min-h-[44px] min-w-[44px] flex items-center justify-center h-10 w-10 rounded-full text-muted hover:bg-surface-hover disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 focus:outline-none focus:ring-3 focus:ring-focus"
          title={
            isServerOnline === false ? "Server offline - upload unavailable" : "Upload document"
          }
          aria-label="Upload document"
        >
          <Paperclip size={20} />
        </button>
      </div>

      {/* Submit Button - Right Side */}
      <button
        type="submit"
        disabled={isQuerying || !query.trim() || !userId || isChatDisabled}
        className={`min-h-[44px] min-w-[44px] flex items-center justify-center h-10 w-10 rounded-full transition-all duration-200 focus:outline-none focus:ring-3 focus:ring-focus ${
          isQuerying || !query.trim() || !userId || isChatDisabled
            ? "bg-raised text-quiet cursor-not-allowed"
            : "bg-accent text-on-accent hover:bg-accent-hover"
        }`}
        title="Send message"
        aria-label="Send message"
      >
        {isQuerying ? <Loader size={20} className="animate-spin" /> : <CornerDownLeft size={20} />}
      </button>
    </div>
  );
};
