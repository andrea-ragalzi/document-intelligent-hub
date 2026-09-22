import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { RightSidebar } from "@/components/RightSidebar";

vi.mock("@/contexts/AuthContext", () => ({
  useAuth: () => ({ user: null, logout: vi.fn() }),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

const defaultProps = {
  userId: "guest-a",
  theme: "light" as const,
  isOpen: true,
  onClose: vi.fn(),
  onToggleTheme: vi.fn(),
  documents: [
    {
      filename: "01_InGen.pdf",
      chunks_count: 2,
      is_demo_document: true,
    },
  ],
  onDeleteDocument: vi.fn(),
  onPreviewDocument: vi.fn().mockResolvedValue(undefined),
  onDownloadDocument: vi.fn().mockResolvedValue(undefined),
  onDeleteAccount: vi.fn(),
  onOpenBugReport: vi.fn(),
  onOpenFeedback: vi.fn(),
  tier: "FREE" as const,
  tierLimits: {
    maxDocuments: 5,
    maxQueriesPerDay: 20,
    canUploadMultiple: false,
    hasAdvancedFeatures: false,
  },
  isTierLoading: false,
  isGuest: true,
};

describe("RightSidebar", () => {
  it("opens directly on demo documents when requested", () => {
    render(<RightSidebar {...defaultProps} requestedView="documents" requestedViewRevision={1} />);

    expect(screen.getByRole("heading", { name: "Documents" })).toBeInTheDocument();
    expect(screen.getByText("01_InGen.pdf")).toBeInTheDocument();
    expect(screen.queryByText("Delete")).not.toBeInTheDocument();
  });
});
