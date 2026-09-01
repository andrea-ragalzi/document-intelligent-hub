import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const themedSourceFiles = [
  "app/about/page.tsx",
  "components/BugReportModal.tsx",
  "components/BugReportModal/BugReportFileAttachment.tsx",
  "components/BugReportModal/BugReportModalHeader.tsx",
  "components/BugReportModal/BugReportModalInfo.tsx",
  "components/ChatSection/ChatLoadingSkeleton.tsx",
  "components/DeleteAccountModal.tsx",
  "components/DocumentList.tsx",
  "components/DocumentList/DocumentContextMenu.tsx",
  "components/DocumentList/DocumentItem.tsx",
  "components/DocumentManager.tsx",
  "components/FeedbackModal.tsx",
  "components/OutputLanguageSelector.tsx",
  "components/RenameModal.tsx",
  "components/UploadModal.tsx",
  "components/UseCaseSelector.tsx",
];

describe("frontend theme", () => {
  it("does not retain purple, indigo, or violet utility classes", () => {
    for (const file of themedSourceFiles) {
      const source = readFileSync(resolve(process.cwd(), file), "utf8");
      expect(source, file).not.toMatch(/\b(?:purple|indigo|violet)-/i);
    }
  });

  it("keeps visited links within the application color system", () => {
    const globalStyles = readFileSync(resolve(process.cwd(), "app/globals.css"), "utf8");
    expect(globalStyles).toMatch(/a:visited\s*\{\s*color:\s*inherit;/);
  });
});
