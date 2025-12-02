/**
 * Test suite for BugReportModal component
 * Tests file upload, validation, and submission
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor, fireEvent, act } from "@testing-library/react";
import "@testing-library/jest-dom";
import { BugReportModal } from "@/components/BugReportModal";

// Mock fetch globally
globalThis.fetch = vi.fn();

describe("BugReportModal", () => {
  const mockOnClose = vi.fn();
  const defaultProps = {
    isOpen: true,
    onClose: mockOnClose,
    conversationId: "test-conv-123",
    userId: "test-user-456",
  };

  beforeEach(() => {
    vi.clearAllMocks();
    (globalThis.fetch as any).mockClear();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe("Rendering", () => {
    it("should not render when isOpen is false", () => {
      const { container } = render(<BugReportModal {...defaultProps} isOpen={false} />);
      expect(container.firstChild).toBeNull();
    });

    it("should render modal when isOpen is true", () => {
      render(<BugReportModal {...defaultProps} />);
      expect(screen.getByText("Report a Bug")).toBeInTheDocument();
    });

    it("should show conversation ID when provided", () => {
      render(<BugReportModal {...defaultProps} />);
      const elements = screen.getAllByText(/test-conv-123/);
      expect(elements.length).toBeGreaterThan(0);
    });

    it("should show file upload section", () => {
      render(<BugReportModal {...defaultProps} />);
      expect(screen.getByText(/Attach File \(optional, max 10MB\)/)).toBeInTheDocument();
    });

    it("should show supported file types", () => {
      render(<BugReportModal {...defaultProps} />);
      expect(screen.getByText(/Images, PDF, Videos.*Archives/)).toBeInTheDocument();
    });
  });

  describe("Form Validation", () => {
    it("should disable submit button when description is less than 10 characters", () => {
      render(<BugReportModal {...defaultProps} />);
      const textarea = screen.getByPlaceholderText(/What went wrong/);
      const submitButton = screen.getByText("Submit Report");

      fireEvent.change(textarea, { target: { value: "Short" } });

      expect(submitButton).toBeDisabled();
    });

    it("should enable submit button when description is 10+ characters", () => {
      render(<BugReportModal {...defaultProps} />);
      const textarea = screen.getByPlaceholderText(/What went wrong/);
      const submitButton = screen.getByText("Submit Report");

      fireEvent.change(textarea, {
        target: { value: "This is a valid bug description" },
      });

      expect(submitButton).not.toBeDisabled();
    });

    it("should show character count with correct color", () => {
      render(<BugReportModal {...defaultProps} />);
      const textarea = screen.getByPlaceholderText(/What went wrong/);

      // Less than 10 chars - should be red
      fireEvent.change(textarea, { target: { value: "Test" } });
      const shortCount = screen.getByText(content => content.includes("4 / 10 chars"));
      expect(shortCount).toHaveClass("text-red-600");

      // 10+ chars - should be green
      fireEvent.change(textarea, {
        target: { value: "Valid description here" },
      });
      // "Valid description here" is 22 chars
      const validCount = screen.getByText(content => content.includes("22 / 10 chars"));
      expect(validCount).toHaveClass("text-green-600");
    });
  });

  describe("File Upload", () => {
    it("should accept valid file types", () => {
      render(<BugReportModal {...defaultProps} />);
      const fileInput = document.getElementById("bug-file-input") as HTMLInputElement;

      const validFile = new File(["test content"], "test.png", {
        type: "image/png",
      });

      Object.defineProperty(fileInput, "files", {
        value: [validFile],
        writable: false,
      });

      fireEvent.change(fileInput);

      waitFor(() => {
        expect(screen.getByText("test.png")).toBeInTheDocument();
      });
    });

    it("should show file size in MB", async () => {
      render(<BugReportModal {...defaultProps} />);
      const fileInput = document.getElementById("bug-file-input") as HTMLInputElement;

      // Create a 2MB file
      const largeFile = new File(["x".repeat(2 * 1024 * 1024)], "large.jpg", {
        type: "image/jpeg",
      });

      Object.defineProperty(fileInput, "files", {
        value: [largeFile],
        writable: false,
      });

      fireEvent.change(fileInput);

      await waitFor(() => {
        expect(screen.getByText(/2\.00 MB/)).toBeInTheDocument();
      });
    });

    it("should show error message when file is too large", async () => {
      render(<BugReportModal {...defaultProps} />);
      const fileInput = document.getElementById("bug-file-input") as HTMLInputElement;

      // Create an 11MB file
      const tooLargeFile = new File(["x".repeat(11 * 1024 * 1024)], "huge.mp4", {
        type: "video/mp4",
      });

      Object.defineProperty(fileInput, "files", {
        value: [tooLargeFile],
        writable: false,
      });

      fireEvent.change(fileInput);

      await waitFor(() => {
        expect(screen.getByText(/File too large/)).toBeInTheDocument();
      });
    });

    it("should NOT disable submit when file is too large (file is rejected)", async () => {
      render(<BugReportModal {...defaultProps} />);
      const textarea = screen.getByPlaceholderText(/What went wrong/);
      const fileInput = document.getElementById("bug-file-input") as HTMLInputElement;

      // Valid description
      fireEvent.change(textarea, {
        target: { value: "Valid description here" },
      });

      // File too large
      const tooLargeFile = new File(["x".repeat(11 * 1024 * 1024)], "huge.zip", {
        type: "application/zip",
      });

      Object.defineProperty(fileInput, "files", {
        value: [tooLargeFile],
        writable: false,
      });

      fireEvent.change(fileInput);

      await waitFor(() => {
        const submitButton = screen.getByText("Submit Report");
        // Button should be enabled because the invalid file was rejected
        expect(submitButton).not.toBeDisabled();
        // And error message should be shown
        expect(screen.getByText(/File too large/)).toBeInTheDocument();
      });
    });

    it('should show "Too large!" warning in error message for oversized files', async () => {
      render(<BugReportModal {...defaultProps} />);
      const fileInput = document.getElementById("bug-file-input") as HTMLInputElement;

      const tooLargeFile = new File(["x".repeat(12 * 1024 * 1024)], "too-large.pdf", {
        type: "application/pdf",
      });

      Object.defineProperty(fileInput, "files", {
        value: [tooLargeFile],
        writable: false,
      });

      fireEvent.change(fileInput);

      await waitFor(() => {
        expect(screen.getByText(/File too large/)).toBeInTheDocument();
      });
    });

    it("should allow removing attached file", async () => {
      render(<BugReportModal {...defaultProps} />);
      const fileInput = document.getElementById("bug-file-input") as HTMLInputElement;

      const validFile = new File(["test"], "test.png", { type: "image/png" });

      Object.defineProperty(fileInput, "files", {
        value: [validFile],
        writable: false,
      });

      fireEvent.change(fileInput);

      await waitFor(() => {
        expect(screen.getByText("test.png")).toBeInTheDocument();
      });

      // Click remove button
      const removeButtons = screen.getAllByRole("button");
      const removeButton = removeButtons.find(btn => btn.querySelector("svg")); // X icon

      if (removeButton) {
        fireEvent.click(removeButton);
      }

      await waitFor(() => {
        expect(screen.queryByText("test.png")).not.toBeInTheDocument();
      });
    });

    it("should reject invalid file types", async () => {
      render(<BugReportModal {...defaultProps} />);
      const fileInput = document.getElementById("bug-file-input") as HTMLInputElement;

      const invalidFile = new File(["test"], "test.exe", {
        type: "application/x-msdownload",
      });

      Object.defineProperty(fileInput, "files", {
        value: [invalidFile],
        writable: false,
      });

      fireEvent.change(fileInput);

      await waitFor(() => {
        expect(
          screen.getByText(/Only images, PDF, videos, and compressed files/)
        ).toBeInTheDocument();
      });
    });
  });

  describe("Form Submission", () => {
    it("should submit bug report without attachment", async () => {
      (globalThis.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          message: "Bug report received successfully",
          report_id: "test-123",
          status: "logged",
          email_sent: true,
          attachment_included: false,
        }),
      });

      render(<BugReportModal {...defaultProps} />);
      const textarea = screen.getByPlaceholderText(/What went wrong/);
      const submitButton = screen.getByText("Submit Report");

      fireEvent.change(textarea, {
        target: { value: "This is a test bug report" },
      });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(globalThis.fetch).toHaveBeenCalledWith(
          expect.stringContaining("/report-bug"),
          expect.objectContaining({
            method: "POST",
            body: expect.any(FormData),
          })
        );
      });
    });

    it("should submit bug report with attachment", async () => {
      (globalThis.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          message: "Bug report received successfully",
          report_id: "test-456",
          status: "logged",
          email_sent: true,
          attachment_included: true,
        }),
      });

      render(<BugReportModal {...defaultProps} />);
      const textarea = screen.getByPlaceholderText(/What went wrong/);
      const fileInput = document.getElementById("bug-file-input") as HTMLInputElement;

      fireEvent.change(textarea, {
        target: { value: "Bug with screenshot attached" },
      });

      const validFile = new File(["image data"], "screenshot.png", {
        type: "image/png",
      });
      Object.defineProperty(fileInput, "files", {
        value: [validFile],
        writable: false,
      });
      fireEvent.change(fileInput);

      await waitFor(() => {
        const submitButton = screen.getByText("Submit Report");
        fireEvent.click(submitButton);
      });

      await waitFor(() => {
        expect(globalThis.fetch).toHaveBeenCalled();
        const formData = (globalThis.fetch as any).mock.calls[0][1].body;
        expect(formData).toBeInstanceOf(FormData);
      });
    });

    it("should handle 413 error with user-friendly message", async () => {
      (globalThis.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 413,
      });

      render(<BugReportModal {...defaultProps} />);
      const textarea = screen.getByPlaceholderText(/What went wrong/);
      const submitButton = screen.getByText("Submit Report");

      fireEvent.change(textarea, {
        target: { value: "Test submission with large file" },
      });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/File too large.*Maximum size is 10MB/)).toBeInTheDocument();
      });
    });

    it("should show success message after submission", async () => {
      (globalThis.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          message: "Bug report received successfully",
          report_id: "test-789",
          status: "logged",
          email_sent: true,
        }),
      });

      render(<BugReportModal {...defaultProps} />);
      const textarea = screen.getByPlaceholderText(/What went wrong/);
      const submitButton = screen.getByText("Submit Report");

      fireEvent.change(textarea, {
        target: { value: "Successful bug report" },
      });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/submitted successfully/)).toBeInTheDocument();
      });
    });

    it("should close modal after successful submission", async () => {
      // Spy on setTimeout instead of using fake timers
      const setTimeoutSpy = vi.spyOn(globalThis, "setTimeout");

      (globalThis.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          message: "Bug report received successfully",
          status: "logged",
        }),
      });

      render(<BugReportModal {...defaultProps} />);
      const textarea = screen.getByPlaceholderText(/What went wrong/);
      const submitButton = screen.getByText("Submit Report");

      fireEvent.change(textarea, { target: { value: "Test auto-close" } });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/submitted successfully/)).toBeInTheDocument();
      });

      // Check if setTimeout was called with 2000ms
      expect(setTimeoutSpy).toHaveBeenCalledWith(expect.any(Function), 2000);

      // Execute the callback manually
      const callback = setTimeoutSpy.mock.calls.find(call => call[1] === 2000)?.[0];
      if (callback) {
        act(() => {
          callback();
        });
      }

      expect(mockOnClose).toHaveBeenCalled();
    });
  });

  describe("User Experience", () => {
    it("should show technical details section", () => {
      render(<BugReportModal {...defaultProps} />);
      expect(screen.getByText(/Technical Details \(click to expand\)/)).toBeInTheDocument();
    });

    it("should show info banner explaining what data is sent", () => {
      render(<BugReportModal {...defaultProps} />);
      expect(screen.getByText(/What will be sent:/)).toBeInTheDocument();
    });

    it("should disable all inputs while submitting", async () => {
      const mockResponse = { ok: true, json: async () => ({}) };
      let resolveFetch: (value: any) => void;
      const pendingPromise = new Promise(resolve => {
        resolveFetch = resolve;
      });
      (globalThis.fetch as any).mockImplementation(() => pendingPromise);

      render(<BugReportModal {...defaultProps} />);
      const textarea = screen.getByPlaceholderText(/What went wrong/);
      const submitButton = screen.getByText("Submit Report");

      fireEvent.change(textarea, {
        target: { value: "Testing disabled state" },
      });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(textarea).toBeDisabled();
        expect(screen.getByText("Sending...")).toBeInTheDocument();
      });

      // Clean up
      await act(async () => {
        resolveFetch!(mockResponse);
      });
    });

    it("should prevent closing modal while submitting", async () => {
      const mockResponse = { ok: true, json: async () => ({}) };
      let resolveFetch: (value: any) => void;
      const pendingPromise = new Promise(resolve => {
        resolveFetch = resolve;
      });
      (globalThis.fetch as any).mockImplementation(() => pendingPromise);

      render(<BugReportModal {...defaultProps} />);
      const textarea = screen.getByPlaceholderText(/What went wrong/);
      const submitButton = screen.getByText("Submit Report");

      fireEvent.change(textarea, {
        target: { value: "Testing close prevention" },
      });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText("Sending...")).toBeInTheDocument();
      });

      // Try to click Cancel button - should be disabled
      const cancelButton = screen.getByText("Cancel");
      expect(cancelButton).toBeDisabled();

      // Clean up
      await act(async () => {
        resolveFetch!(mockResponse);
      });
    });
  });
});
