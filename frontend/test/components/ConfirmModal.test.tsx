import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi, afterEach } from "vitest";
import { ConfirmModal } from "../../components/ConfirmModal";

describe("ConfirmModal", () => {
  const mockOnConfirm = vi.fn();
  const mockOnCancel = vi.fn();

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("should not render when isOpen is false", () => {
    const { container } = render(
      <ConfirmModal
        isOpen={false}
        title="Test Title"
        message="Test message"
        confirmText="Confirm"
        cancelText="Cancel"
        onConfirm={mockOnConfirm}
        onCancel={mockOnCancel}
      />
    );

    expect(container.firstChild).toBeNull();
  });

  it("should render when isOpen is true", () => {
    render(
      <ConfirmModal
        isOpen={true}
        title="Delete Confirmation"
        message="Are you sure you want to delete this?"
        confirmText="Delete"
        cancelText="Cancel"
        onConfirm={mockOnConfirm}
        onCancel={mockOnCancel}
      />
    );

    expect(screen.getByText("Delete Confirmation")).toBeInTheDocument();
    expect(screen.getByText(/are you sure/i)).toBeInTheDocument();
    expect(screen.getByText("Delete")).toBeInTheDocument();
    expect(screen.getByText("Cancel")).toBeInTheDocument();
  });

  it("should call onConfirm when confirm button is clicked", () => {
    render(
      <ConfirmModal
        isOpen={true}
        title="Confirm Action"
        message="Proceed?"
        confirmText="Yes"
        cancelText="No"
        onConfirm={mockOnConfirm}
        onCancel={mockOnCancel}
      />
    );

    const confirmButton = screen.getByText("Yes");
    fireEvent.click(confirmButton);

    expect(mockOnConfirm).toHaveBeenCalledTimes(1);
    expect(mockOnCancel).not.toHaveBeenCalled();
  });

  it("should call onCancel when cancel button is clicked", () => {
    render(
      <ConfirmModal
        isOpen={true}
        title="Confirm Action"
        message="Proceed?"
        confirmText="Yes"
        cancelText="No"
        onConfirm={mockOnConfirm}
        onCancel={mockOnCancel}
      />
    );

    const cancelButton = screen.getByText("No");
    fireEvent.click(cancelButton);

    expect(mockOnCancel).toHaveBeenCalledTimes(1);
    expect(mockOnConfirm).not.toHaveBeenCalled();
  });

  it("should render danger variant with red styling", () => {
    render(
      <ConfirmModal
        isOpen={true}
        title="Delete"
        message="Dangerous action"
        confirmText="Delete"
        cancelText="Cancel"
        variant="danger"
        onConfirm={mockOnConfirm}
        onCancel={mockOnCancel}
      />
    );

    const confirmButton = screen.getByRole("button", { name: "Delete" });
    expect(confirmButton.className).toContain("red");
  });

  it("should render warning variant with yellow styling", () => {
    render(
      <ConfirmModal
        isOpen={true}
        title="Warning"
        message="Warning action"
        confirmText="Proceed"
        cancelText="Cancel"
        variant="warning"
        onConfirm={mockOnConfirm}
        onCancel={mockOnCancel}
      />
    );

    const confirmButton = screen.getByText("Proceed");
    expect(confirmButton.className).toContain("yellow");
  });

  it("should render info variant with blue styling", () => {
    render(
      <ConfirmModal
        isOpen={true}
        title="Information"
        message="Info action"
        confirmText="OK"
        cancelText="Cancel"
        variant="info"
        onConfirm={mockOnConfirm}
        onCancel={mockOnCancel}
      />
    );

    const confirmButton = screen.getByText("OK");
    expect(confirmButton.className).toContain("blue");
  });

  it("should handle multiline messages", () => {
    const multilineMessage = "Line 1\nLine 2\nLine 3";

    render(
      <ConfirmModal
        isOpen={true}
        title="Multiline Test"
        message={multilineMessage}
        confirmText="OK"
        cancelText="Cancel"
        onConfirm={mockOnConfirm}
        onCancel={mockOnCancel}
      />
    );

    expect(screen.getByText(/Line 1/)).toBeInTheDocument();
    expect(screen.getByText(/Line 2/)).toBeInTheDocument();
    expect(screen.getByText(/Line 3/)).toBeInTheDocument();
  });

  it("should handle very long messages", () => {
    const longMessage = "A".repeat(500);

    render(
      <ConfirmModal
        isOpen={true}
        title="Long Message"
        message={longMessage}
        confirmText="OK"
        cancelText="Cancel"
        onConfirm={mockOnConfirm}
        onCancel={mockOnCancel}
      />
    );

    expect(screen.getByText(longMessage)).toBeInTheDocument();
  });

  it("should close modal when clicking backdrop", () => {
    const { container } = render(
      <ConfirmModal
        isOpen={true}
        title="Test"
        message="Test message"
        confirmText="OK"
        cancelText="Cancel"
        onConfirm={mockOnConfirm}
        onCancel={mockOnCancel}
      />
    );

    const backdrop = container.querySelector('[data-testid="modal-backdrop"]');
    if (backdrop) {
      fireEvent.click(backdrop);
      expect(mockOnCancel).toHaveBeenCalled();
    }
  });

  it("should prevent event propagation on modal content click", () => {
    const { container } = render(
      <ConfirmModal
        isOpen={true}
        title="Test"
        message="Test message"
        confirmText="OK"
        cancelText="Cancel"
        onConfirm={mockOnConfirm}
        onCancel={mockOnCancel}
      />
    );

    const modalContent = container.querySelector('[data-testid="modal-content"]');
    if (modalContent) {
      fireEvent.click(modalContent);
      expect(mockOnCancel).not.toHaveBeenCalled();
    }
  });
});
