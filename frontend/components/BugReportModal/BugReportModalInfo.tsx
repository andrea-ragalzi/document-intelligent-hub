interface BugReportModalInfoProps {
  conversationId?: string | null;
}

export const BugReportModalInfo: React.FC<BugReportModalInfoProps> = ({ conversationId }) => {
  return (
    <>
      {/* Info Banner */}
      <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
        <p className="text-sm text-blue-900 dark:text-blue-200">
          <strong>ℹ️ What will be sent:</strong> Your bug description + optional file
          (image/video/PDF/archive) + technical context (User ID, Conversation ID, timestamp,
          browser info) will be emailed to our support team.
        </p>
      </div>

      {/* Conversation ID Display (if available) */}
      {conversationId && (
        <div className="p-3 bg-indigo-50 dark:bg-indigo-950 rounded-lg border border-indigo-200 dark:border-indigo-800">
          <p className="text-sm text-indigo-700 dark:text-indigo-300">
            <span className="font-semibold">📍 Current Conversation:</span>{" "}
            <code className="text-xs break-all">{conversationId}</code>
          </p>
        </div>
      )}
    </>
  );
};
