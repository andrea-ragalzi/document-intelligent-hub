export const BugReportModalInfo: React.FC = () => {
  return (
    <>
      {/* Info Banner */}
      <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
        <p className="text-sm text-blue-900 dark:text-blue-200">
          <strong>What will be sent:</strong> Your description, optional screenshot, and safe
          diagnostic context such as the verified account, timestamp, and browser information.
        </p>
      </div>
    </>
  );
};
