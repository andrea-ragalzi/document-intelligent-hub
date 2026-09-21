import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { DocumentsView } from "@/components/RightSidebar/DocumentsView";

const defaultProps = {
  documents: [],
  onDeleteDocument: vi.fn(),
  onPreviewDocument: vi.fn().mockResolvedValue(undefined),
  onDownloadDocument: vi.fn().mockResolvedValue(undefined),
};

describe("DocumentsView", () => {
  it("shows a skeleton instead of an empty document list while documents are loading", () => {
    render(<DocumentsView {...defaultProps} documents={undefined} isLoadingDocuments />);

    expect(screen.getByRole("status", { name: "Loading documents" })).toBeInTheDocument();
    expect(screen.queryByText("No documents uploaded yet")).not.toBeInTheDocument();
  });

  it("shows the empty state after the document request completes with no documents", () => {
    render(<DocumentsView {...defaultProps} isLoadingDocuments={false} />);

    expect(screen.getByText("No documents uploaded yet")).toBeInTheDocument();
  });
});
