import { render, screen } from "@testing-library/react";
import type { ComponentProps } from "react";
import { describe, expect, it, vi } from "vitest";
import { ChatSection } from "@/components/ChatSection";

vi.mock("@/components/ChatSection/useChatScroll", () => ({
  useChatScroll: () => ({ current: null }),
}));

const defaultProps: ComponentProps<typeof ChatSection> = {
  chatHistory: [],
  query: "",
  isQuerying: false,
  userId: "user-a",
  onQueryChange: vi.fn(),
  onQuerySubmit: vi.fn(),
  hasDocuments: true,
  isCheckingDocuments: false,
  onOpenUploadModal: vi.fn(),
  demoDocumentState: "idle",
  suggestedQuestions: [],
  onSuggestedQuestion: vi.fn(),
};

const renderChatSection = (overrides: Partial<ComponentProps<typeof ChatSection>> = {}) =>
  render(<ChatSection {...defaultProps} {...overrides} />);

describe("ChatSection", () => {
  it("renders one chat icon in the new-conversation empty state", () => {
    const { container } = renderChatSection();

    expect(container.querySelectorAll("svg.lucide-message-square")).toHaveLength(1);
  });

  it("keeps the initial document check in a stable loading state", () => {
    renderChatSection({ hasDocuments: false, isCheckingDocuments: true });

    expect(screen.getByRole("status", { name: "Loading document workspace" })).toBeInTheDocument();
    expect(screen.queryByText("No documents uploaded yet")).not.toBeInTheDocument();
  });

  it("does not show an empty workspace while the private demo document is provisioning", () => {
    renderChatSection({ hasDocuments: false, demoDocumentState: "seeding" });

    expect(screen.getByText("Preparing your private demo document…")).toBeInTheDocument();
    expect(screen.queryByText("No documents uploaded yet")).not.toBeInTheDocument();
  });

  it("shows the authoritative guest allowance beside the mobile composer", () => {
    renderChatSection({
      isGuest: true,
      guestQuotaRemaining: 5,
      guestQuotaLimited: true,
    });

    expect(screen.getByText("5 questions remaining today")).toBeInTheDocument();
    expect(screen.getByText("5 questions remaining today")).toHaveClass("sm:hidden");
  });

  it("shows zero remaining guest questions and hides allowance for registered users", () => {
    const { rerender } = renderChatSection({
      isGuest: true,
      guestQuotaRemaining: 0,
      guestQuotaLimited: true,
    });

    expect(screen.getByText("0 questions remaining today")).toBeInTheDocument();

    rerender(<ChatSection {...defaultProps} guestQuotaRemaining={5} guestQuotaLimited />);
    expect(screen.queryByText("5 questions remaining today")).not.toBeInTheDocument();
  });

  it("lets the empty guest demo flow into the composer on mobile", () => {
    const { container } = renderChatSection({ isGuest: true });
    const scrollArea = container.firstElementChild?.firstElementChild;

    expect(scrollArea).toHaveClass("flex-1");
  });

  it("renders repeated assistant text without duplicate React keys", () => {
    const consoleError = vi.spyOn(console, "error").mockImplementation(() => undefined);

    renderChatSection({
      chatHistory: [
        { type: "user", text: "Question one", sources: [] },
        { type: "assistant", text: "No answer found", sources: [] },
        { type: "user", text: "Question two", sources: [] },
        { type: "assistant", text: "No answer found", sources: [] },
      ],
    });

    expect(
      consoleError.mock.calls.some(([message]) =>
        String(message).includes("Encountered two children with the same key")
      )
    ).toBe(false);
    consoleError.mockRestore();
  });

  it("uses a shrinkable scroll area and a safe-area-aware composer", () => {
    const { container } = renderChatSection();

    const chatRoot = container.firstElementChild;
    const scrollArea = chatRoot?.firstElementChild;
    const composer = container.querySelector("form");

    expect(chatRoot).toHaveClass("min-h-0");
    expect(scrollArea).toHaveClass("min-h-0", "flex-1");
    expect(scrollArea).not.toHaveAttribute("style");
    expect(composer).toHaveClass("shrink-0", "pb-[max(0.75rem,env(safe-area-inset-bottom))]");
  });
});
