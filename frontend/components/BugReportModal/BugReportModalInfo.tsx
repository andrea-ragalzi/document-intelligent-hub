export const BugReportModalInfo: React.FC = () => {
  return (
    <>
      {/* Info Banner */}
      <div className="rounded-lg border border-line/20 bg-raised p-3">
        <p className="text-sm text-ink">
          <strong>What will be sent:</strong> Your description, optional screenshot, and safe
          diagnostic context such as the verified account, timestamp, and browser information.
        </p>
      </div>
    </>
  );
};
