interface BugReportStatusMessagesProps {
  submitStatus: "idle" | "success" | "error";
  errorMessage: string;
}

export const BugReportStatusMessages: React.FC<BugReportStatusMessagesProps> = ({
  submitStatus,
  errorMessage,
}) => {
  if (submitStatus === "success") {
    return (
      <div className="p-3 bg-green-100 dark:bg-green-900/30 border border-green-300 dark:border-green-700 rounded-lg">
        <p className="text-sm font-medium text-green-800 dark:text-green-200">
          ✓ Bug report submitted successfully! Email sent to support team.
        </p>
      </div>
    );
  }

  if (submitStatus === "error") {
    return (
      <div className="p-3 bg-red-100 dark:bg-red-900/30 border border-red-300 dark:border-red-700 rounded-lg">
        <p className="text-sm font-medium text-red-800 dark:text-red-200">
          ✗{" "}
          {errorMessage ||
            "Failed to submit report. Please provide at least 10 characters description."}
        </p>
      </div>
    );
  }

  return null;
};
