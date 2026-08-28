import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { DemoDocumentCard } from "@/components/ChatSection/DemoDocumentCard";

const questions = [
  "What does Alice first notice about the Cheshire Cat?",
  "How is the Cheshire Cat described?",
  "What happens when the Cat disappears?",
];

describe("DemoDocumentCard", () => {
  it("shows the private demo and its three suggested questions", () => {
    render(
      <DemoDocumentCard
        state="ready"
        suggestedQuestions={questions}
        onSelectQuestion={vi.fn()}
        onOpenUpload={vi.fn()}
      />
    );

    expect(screen.getByText("Demo document ready")).toBeInTheDocument();
    for (const question of questions) {
      expect(screen.getByRole("button", { name: question })).toBeInTheDocument();
    }
    expect(screen.getByRole("button", { name: /upload your own pdf/i })).toBeInTheDocument();
  });

  it("keeps upload available when seeding fails", async () => {
    const user = userEvent.setup();
    const onOpenUpload = vi.fn();
    render(
      <DemoDocumentCard
        state="failed"
        suggestedQuestions={[]}
        onSelectQuestion={vi.fn()}
        onOpenUpload={onOpenUpload}
      />
    );

    await user.click(screen.getByRole("button", { name: /upload your own pdf/i }));
    expect(onOpenUpload).toHaveBeenCalledOnce();
  });
});
