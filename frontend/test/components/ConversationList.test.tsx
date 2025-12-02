import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi, afterEach } from "vitest";
import { ConversationList } from "../../components/ConversationList";
import type { SavedConversation } from "../../lib/types";

describe("ConversationList", () => {
  const mockOnLoad = vi.fn();
  const mockOnDelete = vi.fn();
  const mockOnRename = vi.fn();
  const mockOnPin = vi.fn();

  const mockConversations: SavedConversation[] = [
    {
      id: "conv-1",
      userId: "user-123",
      name: "First Conversation",
      timestamp: "2025-01-01 10:00:00",
      history: [
        { type: "user", text: "Hello", sources: [] },
        { type: "assistant", text: "Hi!", sources: [] },
      ],
    },
    {
      id: "conv-2",
      userId: "user-123",
      name: "Second Conversation",
      timestamp: "2025-01-02 14:30:00",
      history: [
        { type: "user", text: "How are you?", sources: [] },
        { type: "assistant", text: "I am well!", sources: [] },
      ],
    },
  ];

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("should render empty state when no conversations", () => {
    render(
      <ConversationList
        onPin={mockOnPin}
        conversations={[]}
        onLoad={mockOnLoad}
        onDelete={mockOnDelete}
        onRename={mockOnRename}
      />
    );

    expect(screen.getByText(/no saved conversations/i)).toBeInTheDocument();
  });

  it("should render list of conversations", () => {
    render(
      <ConversationList
        onPin={mockOnPin}
        conversations={mockConversations}
        onLoad={mockOnLoad}
        onDelete={mockOnDelete}
        onRename={mockOnRename}
      />
    );

    expect(screen.getByText("First Conversation")).toBeInTheDocument();
    expect(screen.getByText("Second Conversation")).toBeInTheDocument();
    expect(screen.getByText("2025-01-01 10:00:00")).toBeInTheDocument();
    expect(screen.getByText("2025-01-02 14:30:00")).toBeInTheDocument();
  });

  it("should call onLoad when conversation card is clicked", () => {
    render(
      <ConversationList
        onPin={mockOnPin}
        conversations={mockConversations}
        onLoad={mockOnLoad}
        onDelete={mockOnDelete}
        onRename={mockOnRename}
      />
    );

    const firstConversationCard = screen.getByText("First Conversation").closest("div");
    fireEvent.click(firstConversationCard!);

    expect(mockOnLoad).toHaveBeenCalledWith(mockConversations[0]);
    expect(mockOnLoad).toHaveBeenCalledTimes(1);
  });

  it("should call onDelete when delete action is taken from the menu", () => {
    render(
      <ConversationList
        onPin={mockOnPin}
        conversations={mockConversations}
        onLoad={mockOnLoad}
        onDelete={mockOnDelete}
        onRename={mockOnRename}
      />
    );

    const kebabButtons = screen.getAllByTitle("Options");
    fireEvent.click(kebabButtons[1]);

    const deleteAction = screen.getByRole("button", { name: /^delete$/i });
    fireEvent.click(deleteAction);

    const confirmDelete = screen.getByRole("button", { name: /^delete$/i });
    fireEvent.click(confirmDelete);

    expect(mockOnDelete).toHaveBeenCalledWith("conv-1", "First Conversation");
    expect(mockOnDelete).toHaveBeenCalledTimes(1);
    expect(mockOnLoad).not.toHaveBeenCalled(); // Should not trigger card click
  });

  it("should keep the menu open when interacting with its actions", () => {
    render(
      <ConversationList
        onPin={mockOnPin}
        conversations={mockConversations}
        onLoad={mockOnLoad}
        onDelete={mockOnDelete}
        onRename={mockOnRename}
      />
    );

    const kebabButtons = screen.getAllByTitle("Options");
    fireEvent.click(kebabButtons[0]);

    const deleteAction = screen.getByRole("button", { name: /^delete$/i });
    fireEvent.mouseDown(deleteAction);

    expect(screen.getByRole("button", { name: /^delete$/i })).toBeInTheDocument();
  });

  it("should call onRename when rename action is taken from the menu", () => {
    render(
      <ConversationList
        onPin={mockOnPin}
        conversations={mockConversations}
        onLoad={mockOnLoad}
        onDelete={mockOnDelete}
        onRename={mockOnRename}
      />
    );

    const kebabButtons = screen.getAllByTitle("Options");
    fireEvent.click(kebabButtons[0]);

    const renameAction = screen.getByRole("button", { name: /rename/i });
    fireEvent.click(renameAction);

    expect(mockOnRename).toHaveBeenCalledWith("conv-2", "Second Conversation");
    expect(mockOnRename).toHaveBeenCalledTimes(1);
    expect(mockOnLoad).not.toHaveBeenCalled(); // Should not trigger card click
  });

  it("should render all action buttons for each conversation", () => {
    render(
      <ConversationList
        onPin={mockOnPin}
        conversations={mockConversations}
        onLoad={mockOnLoad}
        onDelete={mockOnDelete}
        onRename={mockOnRename}
      />
    );

    const kebabButtons = screen.getAllByTitle("Options");
    fireEvent.click(kebabButtons[0]);

    expect(screen.getByRole("button", { name: /pin/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /rename/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /delete/i })).toBeInTheDocument();
  });

  it("should truncate long conversation names", () => {
    const longNameConversations: SavedConversation[] = [
      {
        id: "conv-long",
        userId: "user-123",
        name: "This is a very long conversation name that should be truncated",
        timestamp: "2025-01-01",
        history: [],
      },
    ];

    const { container } = render(
      <ConversationList
        onPin={mockOnPin}
        conversations={longNameConversations}
        onLoad={mockOnLoad}
        onDelete={mockOnDelete}
        onRename={mockOnRename}
      />
    );

    const nameElement = screen.getByText(/this is a very long conversation name/i);
    expect(nameElement).toBeInTheDocument();
    expect(nameElement.className).toContain("truncate");
  });

  it("should display section header", () => {
    render(
      <ConversationList
        onPin={mockOnPin}
        conversations={mockConversations}
        onLoad={mockOnLoad}
        onDelete={mockOnDelete}
        onRename={mockOnRename}
      />
    );

    expect(screen.getByText(/conversations/i)).toBeInTheDocument();
  });

  it("should handle single conversation", () => {
    render(
      <ConversationList
        onPin={mockOnPin}
        conversations={[mockConversations[0]]}
        onLoad={mockOnLoad}
        onDelete={mockOnDelete}
        onRename={mockOnRename}
      />
    );

    expect(screen.getByText("First Conversation")).toBeInTheDocument();
    expect(screen.queryByText("Second Conversation")).not.toBeInTheDocument();
  });

  it("should render conversations in correct order", () => {
    render(
      <ConversationList
        onPin={mockOnPin}
        conversations={mockConversations}
        onLoad={mockOnLoad}
        onDelete={mockOnDelete}
        onRename={mockOnRename}
      />
    );

    const names = screen
      .getAllByText(/conversation/i)
      .filter(el => el.className.includes("font-semibold"));

    expect(names[0]).toHaveTextContent("Second Conversation");
    expect(names[1]).toHaveTextContent("First Conversation");
  });

  it("should apply hover styles and cursor pointer to conversation items", () => {
    const { container } = render(
      <ConversationList
        onPin={mockOnPin}
        conversations={mockConversations}
        onLoad={mockOnLoad}
        onDelete={mockOnDelete}
        onRename={mockOnRename}
      />
    );

    const conversationCards = container.querySelectorAll('[class*="cursor-pointer"]');
    expect(conversationCards.length).toBe(2); // One for each conversation
  });

  it("should handle empty conversation history", () => {
    const emptyHistoryConv: SavedConversation[] = [
      {
        id: "empty",
        userId: "user-123",
        name: "Empty Conversation",
        timestamp: "2025-01-01",
        history: [],
      },
    ];

    render(
      <ConversationList
        onPin={mockOnPin}
        conversations={emptyHistoryConv}
        onLoad={mockOnLoad}
        onDelete={mockOnDelete}
        onRename={mockOnRename}
      />
    );

    expect(screen.getByText("Empty Conversation")).toBeInTheDocument();
  });
});
