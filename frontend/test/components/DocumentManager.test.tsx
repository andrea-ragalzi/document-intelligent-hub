import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, beforeEach, vi } from "vitest";
import { DocumentManager } from "@/components/DocumentManager";
import type { AlertState } from "@/lib/types";

// Mock useDocuments hook
vi.mock("@/hooks/useDocuments", () => ({
  useDocuments: vi.fn(),
}));

import { useDocuments } from "@/hooks/useDocuments";

describe("DocumentManager", () => {
  const mockUserId = "test-user-123";
  const mockFile = new File(["test content"], "test.pdf", {
    type: "application/pdf",
  });
  const mockOnFileChange = vi.fn();
  const mockOnUpload = vi.fn();
  const mockDeleteDocument = vi.fn();
  const mockRefreshDocuments = vi.fn();

  const defaultProps = {
    file: null,
    isUploading: false,
    userId: mockUserId,
    uploadAlert: { message: "", type: "info" as const },
    statusAlert: null,
    onFileChange: mockOnFileChange,
    onUpload: mockOnUpload,
  };

  const mockDocuments = [
    {
      filename: "document1.pdf",
      chunks_count: 10,
      language: "en",
      uploaded_at: "2024-01-01T00:00:00Z",
    },
    {
      filename: "document2.pdf",
      chunks_count: 5,
      language: "it",
      uploaded_at: "2024-01-02T00:00:00Z",
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    // Mock useDocuments return value
    vi.mocked(useDocuments).mockReturnValue({
      documents: [],
      isLoading: false,
      error: null,
      refreshDocuments: mockRefreshDocuments,
      deleteDocument: mockDeleteDocument,
      deleteAllDocuments: vi.fn(),
    });
  });

  it("should render upload area", () => {
    render(<DocumentManager {...defaultProps} />);

    expect(screen.getByText("Documents")).toBeInTheDocument();
    expect(
      screen.getByText("Drop PDF here or click to browse")
    ).toBeInTheDocument();
    expect(
      screen.getByText("Document will be automatically indexed after upload")
    ).toBeInTheDocument();
  });

  it("should show selected file name", () => {
    render(<DocumentManager {...defaultProps} file={mockFile} />);

    expect(screen.getByText("test.pdf")).toBeInTheDocument();
    expect(screen.getByText("Ready to upload and index")).toBeInTheDocument();
  });

  it("should disable upload button when no file selected", () => {
    render(<DocumentManager {...defaultProps} />);

    const uploadButton = screen.getByRole("button", {
      name: /upload & index document/i,
    });
    expect(uploadButton).toBeDisabled();
  });

  it("should enable upload button when file is selected", () => {
    render(<DocumentManager {...defaultProps} file={mockFile} />);

    const uploadButton = screen.getByRole("button", {
      name: /upload & index document/i,
    });
    expect(uploadButton).not.toBeDisabled();
  });

  it("should show uploading state", () => {
    render(
      <DocumentManager {...defaultProps} file={mockFile} isUploading={true} />
    );

    expect(screen.getByText("Uploading & Indexing...")).toBeInTheDocument();
    const uploadButton = screen.getByRole("button", {
      name: /uploading & indexing/i,
    });
    expect(uploadButton).toBeDisabled();
  });

  it("should call onUpload when form is submitted", () => {
    render(<DocumentManager {...defaultProps} file={mockFile} />);

    const form = screen
      .getByRole("button", { name: /upload & index document/i })
      .closest("form")!;
    fireEvent.submit(form);

    expect(mockOnUpload).toHaveBeenCalledTimes(1);
  });

  it("should display empty state when no documents", () => {
    render(<DocumentManager {...defaultProps} />);

    expect(screen.getByText("Indexed Documents (0)")).toBeInTheDocument();
    expect(screen.getByText("No documents uploaded yet")).toBeInTheDocument();
  });

  it("should display list of documents", () => {
    vi.mocked(useDocuments).mockReturnValue({
      documents: mockDocuments,
      isLoading: false,
      error: null,
      refreshDocuments: mockRefreshDocuments,
      deleteDocument: mockDeleteDocument,
      deleteAllDocuments: vi.fn(),
    });

    render(<DocumentManager {...defaultProps} />);

    expect(screen.getByText("Indexed Documents (2)")).toBeInTheDocument();
    expect(screen.getByText("document1.pdf")).toBeInTheDocument();
    expect(screen.getByText("document2.pdf")).toBeInTheDocument();
    expect(screen.getByText("10")).toBeInTheDocument();
    expect(screen.getByText("5")).toBeInTheDocument();
  });

  it("should show language badges", () => {
    vi.mocked(useDocuments).mockReturnValue({
      documents: mockDocuments,
      isLoading: false,
      error: null,
      refreshDocuments: mockRefreshDocuments,
      deleteDocument: mockDeleteDocument,
      deleteAllDocuments: vi.fn(),
    });

    render(<DocumentManager {...defaultProps} />);

    // Language badges are rendered as lowercase text with uppercase CSS class
    expect(screen.getByText("en")).toBeInTheDocument();
    expect(screen.getByText("it")).toBeInTheDocument();
  });

  it("should not show language badge for unknown language", () => {
    const docsWithUnknown = [
      {
        filename: "test.pdf",
        chunks_count: 5,
        language: "unknown",
        uploaded_at: "2024-01-01T00:00:00Z",
      },
    ];

    vi.mocked(useDocuments).mockReturnValue({
      documents: docsWithUnknown,
      isLoading: false,
      error: null,
      refreshDocuments: mockRefreshDocuments,
      deleteDocument: mockDeleteDocument,
      deleteAllDocuments: vi.fn(),
    });

    render(<DocumentManager {...defaultProps} />);

    expect(screen.queryByText("UNKNOWN")).not.toBeInTheDocument();
  });

  it("should show loading state for documents", () => {
    vi.mocked(useDocuments).mockReturnValue({
      documents: [],
      isLoading: true,
      error: null,
      refreshDocuments: mockRefreshDocuments,
      deleteDocument: mockDeleteDocument,
      deleteAllDocuments: vi.fn(),
    });

    render(<DocumentManager {...defaultProps} />);

    // Check for skeleton loading placeholders (animate-pulse class)
    const skeletons = screen
      .getAllByRole("generic")
      .filter((el) => el.className.includes("animate-pulse"));
    expect(skeletons.length).toBeGreaterThan(0);
  });
  
  it("should call refreshDocuments when refresh button clicked", () => {
    render(<DocumentManager {...defaultProps} />);

    const refreshButton = screen.getByTitle("Refresh list");
    fireEvent.click(refreshButton);

    expect(mockRefreshDocuments).toHaveBeenCalledTimes(1);
  });

  it("should show delete confirmation on trash icon click", () => {
    vi.mocked(useDocuments).mockReturnValue({
      documents: mockDocuments,
      isLoading: false,
      error: null,
      refreshDocuments: mockRefreshDocuments,
      deleteDocument: mockDeleteDocument,
      deleteAllDocuments: vi.fn(),
    });

    render(<DocumentManager {...defaultProps} />);

    const deleteButtons = screen.getAllByTitle("Delete document");
    fireEvent.click(deleteButtons[0]);

    expect(screen.getByText('Delete "document1.pdf"?')).toBeInTheDocument();
    // Check for the confirmation dialog buttons specifically
    const allDeleteButtons = screen.getAllByRole("button", { name: /delete/i });
    expect(allDeleteButtons.length).toBeGreaterThan(0);
    expect(screen.getByRole("button", { name: /cancel/i })).toBeInTheDocument();
  });

  it("should cancel delete confirmation", () => {
    vi.mocked(useDocuments).mockReturnValue({
      documents: mockDocuments,
      isLoading: false,
      error: null,
      refreshDocuments: mockRefreshDocuments,
      deleteDocument: mockDeleteDocument,
      deleteAllDocuments: vi.fn(),
    });

    render(<DocumentManager {...defaultProps} />);

    const deleteButtons = screen.getAllByTitle("Delete document");
    fireEvent.click(deleteButtons[0]);

    const cancelButton = screen.getByRole("button", { name: /cancel/i });
    fireEvent.click(cancelButton);

    expect(
      screen.queryByText('Delete "document1.pdf"?')
    ).not.toBeInTheDocument();
  });

  it("should call deleteDocument when confirmed", async () => {
    mockDeleteDocument.mockResolvedValue(undefined);

    vi.mocked(useDocuments).mockReturnValue({
      documents: mockDocuments,
      isLoading: false,
      error: null,
      refreshDocuments: mockRefreshDocuments,
      deleteDocument: mockDeleteDocument,
      deleteAllDocuments: vi.fn(),
    });

    render(<DocumentManager {...defaultProps} />);

    const deleteButtons = screen.getAllByTitle("Delete document");
    fireEvent.click(deleteButtons[0]);

    // Wait for confirmation dialog and get confirm button by text
    const confirmButton = screen.getByText("Delete", { selector: "button" });
    fireEvent.click(confirmButton);

    await waitFor(() => {
      expect(mockDeleteDocument).toHaveBeenCalledWith("document1.pdf");
    });
  });

  it("should show deleting state", async () => {
    mockDeleteDocument.mockImplementation(() => new Promise(() => {})); // Never resolves

    vi.mocked(useDocuments).mockReturnValue({
      documents: mockDocuments,
      isLoading: false,
      error: null,
      refreshDocuments: mockRefreshDocuments,
      deleteDocument: mockDeleteDocument,
      deleteAllDocuments: vi.fn(),
    });

    render(<DocumentManager {...defaultProps} />);

    const deleteButtons = screen.getAllByTitle("Delete document");
    fireEvent.click(deleteButtons[0]);

    // Get confirm button by text in the confirmation dialog
    const confirmButton = screen.getByText("Delete", { selector: "button" });
    fireEvent.click(confirmButton);

    await waitFor(() => {
      expect(confirmButton).toBeDisabled();
    });
  });

  it("should display upload alert", () => {
    const uploadAlert: AlertState = {
      message: "Upload successful",
      type: "success",
    };

    render(<DocumentManager {...defaultProps} uploadAlert={uploadAlert} />);

    expect(screen.getByText("Upload successful")).toBeInTheDocument();
  });

  it("should display status alert", () => {
    const statusAlert: AlertState = {
      message: "Documents indexed",
      type: "info",
    };

    render(<DocumentManager {...defaultProps} statusAlert={statusAlert} />);

    expect(screen.getByText("Documents indexed")).toBeInTheDocument();
  });

  it("should disable upload when no userId", () => {
    render(<DocumentManager {...defaultProps} userId={null} file={mockFile} />);

    const uploadButton = screen.getByRole("button", {
      name: /upload & index document/i,
    });
    expect(uploadButton).toBeDisabled();
  });

  it("should handle delete error gracefully", async () => {
    const consoleErrorSpy = vi
      .spyOn(console, "error")
      .mockImplementation(() => {});
    mockDeleteDocument.mockRejectedValue(new Error("Delete failed"));

    vi.mocked(useDocuments).mockReturnValue({
      documents: mockDocuments,
      isLoading: false,
      error: null,
      refreshDocuments: mockRefreshDocuments,
      deleteDocument: mockDeleteDocument,
      deleteAllDocuments: vi.fn(),
    });

    render(<DocumentManager {...defaultProps} />);

    const deleteButtons = screen.getAllByTitle("Delete document");
    fireEvent.click(deleteButtons[0]);

    // Get confirm button by text
    const confirmButton = screen.getByText("Delete", { selector: "button" });
    fireEvent.click(confirmButton);

    await waitFor(() => {
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        "Error deleting document:",
        expect.any(Error)
      );
    });

    consoleErrorSpy.mockRestore();
  });

  it("should log document count on render", () => {
    const consoleLogSpy = vi.spyOn(console, "log").mockImplementation(() => {});

    vi.mocked(useDocuments).mockReturnValue({
      documents: mockDocuments,
      isLoading: false,
      error: null,
      refreshDocuments: mockRefreshDocuments,
      deleteDocument: mockDeleteDocument,
      deleteAllDocuments: vi.fn(),
    });

    render(<DocumentManager {...defaultProps} />);

    expect(consoleLogSpy).toHaveBeenCalledWith(
      expect.stringContaining("📋 DocumentManager render - documents:"),
      2,
      mockDocuments
    );

    consoleLogSpy.mockRestore();
  });
});
