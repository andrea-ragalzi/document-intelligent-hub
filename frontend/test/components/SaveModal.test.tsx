import { render, screen, fireEvent } from "@testing-library/react";
import { SaveModal } from "@/components/SaveModal";
import { describe, it, expect, vi } from "vitest";

describe("SaveModal", () => {
  const mockOnClose = vi.fn();
  const mockOnSave = vi.fn(e => e.preventDefault());
  const mockSetConversationName = vi.fn();

  const defaultProps = {
    isOpen: true,
    conversationName: "My Conversation",
    setConversationName: mockSetConversationName,
    onClose: mockOnClose,
    onSave: mockOnSave,
    errorMessage: "",
  };

  it("should render correctly when isOpen is true", () => {
    render(<SaveModal {...defaultProps} />);
    expect(screen.getByText("Save Chat")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Conversation name (e.g. Q3 Report)")).toBeInTheDocument();
  });

  it("should not render when isOpen is false", () => {
    render(<SaveModal {...defaultProps} isOpen={false} />);
    expect(screen.queryByText("Save Chat")).not.toBeInTheDocument();
  });

  it("should call onClose when the close button is clicked", () => {
    render(<SaveModal {...defaultProps} />);
    fireEvent.click(screen.getByRole("button", { name: /close/i }));
    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it("should call onSave when the form is submitted", () => {
    render(<SaveModal {...defaultProps} />);
    fireEvent.submit(screen.getByRole("button", { name: /save/i }));
    expect(mockOnSave).toHaveBeenCalledTimes(1);
  });

  it("should display an error message when errorMessage is provided", () => {
    render(<SaveModal {...defaultProps} errorMessage="This is an error" />);
    expect(screen.getByText("This is an error")).toBeInTheDocument();
  });

  it("should update the input value correctly", () => {
    render(<SaveModal {...defaultProps} />);
    const input = screen.getByPlaceholderText("Conversation name (e.g. Q3 Report)");
    fireEvent.change(input, { target: { value: "New Name" } });
    expect(mockSetConversationName).toHaveBeenCalledWith("New Name");
  });
});
