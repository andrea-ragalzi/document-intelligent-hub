import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { TopBar } from "@/components/TopBar";

const props = {
  onOpenLeftSidebar: vi.fn(),
  onOpenRightSidebar: vi.fn(),
  onNewConversation: vi.fn(),
  hasConversation: false,
  tier: "FREE" as const,
  isTierLoading: false,
};

describe("TopBar", () => {
  it("hides the conversation navigation control for guests", () => {
    render(<TopBar {...props} isGuest />);

    expect(screen.queryByRole("button", { name: "Toggle navigation" })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Toggle settings" })).toBeInTheDocument();
  });

  it("keeps registered-user navigation unchanged", () => {
    render(<TopBar {...props} />);

    expect(screen.getByRole("button", { name: "Toggle navigation" })).toBeInTheDocument();
  });
});
