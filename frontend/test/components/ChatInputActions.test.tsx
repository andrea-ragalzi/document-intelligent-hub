import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ChatInputActions } from "@/components/ChatSection/ChatInputActions";

describe("ChatInputActions", () => {
  it("hides upload while leaving guest query submission available", () => {
    render(
      <ChatInputActions
        userId="anonymous-recruiter"
        isServerOnline
        isQuerying={false}
        query="What happened?"
        isChatDisabled={false}
        onOpenUploadModal={vi.fn()}
        allowUpload={false}
      />
    );

    expect(screen.queryByRole("button", { name: "Upload document" })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Send message" })).toBeEnabled();
  });
});
