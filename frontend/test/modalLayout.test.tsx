import { fireEvent, render, screen } from "@testing-library/react";
import { useState } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { BugReportModal } from "@/components/BugReportModal";
import { FeedbackModal } from "@/components/FeedbackModal";
import { UploadModal } from "@/components/UploadModal";

vi.mock("@/contexts/AuthContext", () => ({
  useAuth: () => ({ getIdToken: vi.fn() }),
}));

vi.mock("@/components/LanguageSelector", () => ({
  LanguageSelector: () => <div>Document language</div>,
}));

const mobileViewports = [
  { width: 412, height: 915 },
  { width: 412, height: 892 },
];

const UploadModalHarness = () => {
  const [file, setFile] = useState<File | null>(null);

  return (
    <UploadModal
      isOpen
      onClose={vi.fn()}
      file={file}
      isUploading={false}
      uploadAlert={{ message: "Select a PDF to upload.", type: "info" }}
      onFileChange={event => setFile(event.target.files?.[0] ?? null)}
      onUpload={vi.fn()}
      selectedLanguage="en"
      onLanguageChange={vi.fn()}
    />
  );
};

describe("mobile modal scroll layout", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it.each(mobileViewports)(
    "keeps long modal forms scrollable at $width × $height",
    ({ width, height }) => {
      vi.stubGlobal("innerWidth", width);
      vi.stubGlobal("innerHeight", height);

      const { unmount } = render(<UploadModalHarness />);
      fireEvent.change(screen.getByLabelText(/select pdf to upload/i), {
        target: { files: [new File(["pdf"], "guide.pdf", { type: "application/pdf" })] },
      });
      expect(screen.getByText("guide.pdf")).toBeVisible();
      expect(screen.getByTestId("upload-modal-body")).toHaveClass("overflow-y-auto");
      expect(screen.getByTestId("upload-modal-dialog")).toHaveClass("ui-modal-dialog");
      expect(screen.getByRole("button", { name: /upload document/i })).toBeVisible();
      unmount();

      render(<BugReportModal isOpen onClose={vi.fn()} />);
      fireEvent.change(screen.getByLabelText(/attach screenshot/i), {
        target: { files: [new File(["png"], "screen.png", { type: "image/png" })] },
      });
      expect(screen.getByText("screen.png")).toBeVisible();
      expect(screen.getByTestId("bug-report-modal-body")).toHaveClass("overflow-y-auto");
      expect(screen.getByRole("button", { name: /submit report/i })).toBeVisible();
      unmount();

      render(<FeedbackModal isOpen onClose={vi.fn()} />);
      expect(screen.getByTestId("feedback-modal-body")).toHaveClass("overflow-y-auto");
      expect(screen.getByRole("button", { name: /submit feedback/i })).toBeVisible();
    }
  );
});
