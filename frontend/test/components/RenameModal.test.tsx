import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, afterEach } from "vitest";
import { RenameModal } from "../../components/RenameModal";

describe("RenameModal", () => {
  const mockOnClose = vi.fn();
  const mockOnRename = vi.fn();

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("should not render when isOpen is false", () => {
    const { container } = render(
      <RenameModal
        isOpen={false}
        currentName="Test"
        onClose={mockOnClose}
        onRename={mockOnRename}
      />
    );

    expect(container.firstChild).toBeNull();
  });

  it("should render when isOpen is true", () => {
    render(
      <RenameModal
        isOpen={true}
        currentName="Test Conversation"
        onClose={mockOnClose}
        onRename={mockOnRename}
      />
    );

    expect(screen.getByText(/rename conversation/i)).toBeInTheDocument();
    expect(screen.getByDisplayValue("Test Conversation")).toBeInTheDocument();
  });

  it("should display current name in input field", () => {
    render(
      <RenameModal
        isOpen={true}
        currentName="My Original Name"
        onClose={mockOnClose}
        onRename={mockOnRename}
      />
    );

    const input = screen.getByDisplayValue("My Original Name") as HTMLInputElement;
    expect(input).toBeInTheDocument();
    expect(input.value).toBe("My Original Name");
  });

  it("should allow editing the name", () => {
    render(
      <RenameModal
        isOpen={true}
        currentName="Old Name"
        onClose={mockOnClose}
        onRename={mockOnRename}
      />
    );

    const input = screen.getByDisplayValue("Old Name") as HTMLInputElement;

    fireEvent.change(input, { target: { value: "New Name" } });

    expect(input.value).toBe("New Name");
  });

  it("should call onClose when X button is clicked", () => {
    render(
      <RenameModal isOpen={true} currentName="Test" onClose={mockOnClose} onRename={mockOnRename} />
    );

    const closeButton = screen.getByRole("button", { name: "" });
    fireEvent.click(closeButton);

    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it("should call onRename with new name when Rename is clicked", async () => {
    mockOnRename.mockResolvedValue(true);

    render(
      <RenameModal
        isOpen={true}
        currentName="Old Name"
        onClose={mockOnClose}
        onRename={mockOnRename}
      />
    );

    const input = screen.getByDisplayValue("Old Name") as HTMLInputElement;
    fireEvent.change(input, { target: { value: "Updated Name" } });

    const renameButton = screen.getByRole("button", { name: /^rename$/i });
    fireEvent.click(renameButton);

    await waitFor(() => {
      expect(mockOnRename).toHaveBeenCalledWith("Updated Name");
    });
  });

  it("should not submit with empty name", async () => {
    render(
      <RenameModal isOpen={true} currentName="Test" onClose={mockOnClose} onRename={mockOnRename} />
    );

    const input = screen.getByDisplayValue("Test") as HTMLInputElement;
    fireEvent.change(input, { target: { value: "" } });

    const renameButton = screen.getByRole("button", { name: /^rename$/i });
    fireEvent.click(renameButton);

    expect(mockOnRename).not.toHaveBeenCalled();
  });

  it("should not submit with whitespace-only name", async () => {
    render(
      <RenameModal isOpen={true} currentName="Test" onClose={mockOnClose} onRename={mockOnRename} />
    );

    const input = screen.getByDisplayValue("Test") as HTMLInputElement;
    fireEvent.change(input, { target: { value: "   " } });

    const renameButton = screen.getByRole("button", { name: /^rename$/i });
    fireEvent.click(renameButton);

    expect(mockOnRename).not.toHaveBeenCalled();
  });

  it("should handle rename errors gracefully", async () => {
    mockOnRename.mockResolvedValue(false);

    render(
      <RenameModal isOpen={true} currentName="Test" onClose={mockOnClose} onRename={mockOnRename} />
    );

    const input = screen.getByDisplayValue("Test") as HTMLInputElement;
    fireEvent.change(input, { target: { value: "New Name" } });

    const renameButton = screen.getByRole("button", { name: /^rename$/i });
    fireEvent.click(renameButton);

    await waitFor(() => {
      expect(mockOnRename).toHaveBeenCalled();
    });

    // Modal should not close on failure
    expect(mockOnClose).not.toHaveBeenCalled();
  });

  it("should close modal after successful rename", async () => {
    mockOnRename.mockResolvedValue(true);

    render(
      <RenameModal isOpen={true} currentName="Test" onClose={mockOnClose} onRename={mockOnRename} />
    );

    const input = screen.getByDisplayValue("Test") as HTMLInputElement;
    fireEvent.change(input, { target: { value: "Success Name" } });

    const renameButton = screen.getByRole("button", { name: /^rename$/i });
    fireEvent.click(renameButton);

    await waitFor(() => {
      expect(mockOnClose).toHaveBeenCalled();
    });
  });
});
