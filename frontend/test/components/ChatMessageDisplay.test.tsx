import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ChatMessageDisplay } from "@/components/ChatMessageDisplay";

describe("ChatMessageDisplay sources", () => {
  it("renders one filename and retrieved page number in a compact Sources section", () => {
    render(
      <ChatMessageDisplay
        msg={{
          type: "assistant",
          text: "Grounded answer",
          sources: [{ filename: "alice-cheshire-cat-demo.pdf", page_number: 7 }],
        }}
      />
    );

    expect(screen.getByText("Sources")).toBeInTheDocument();
    expect(screen.getByText("alice-cheshire-cat-demo.pdf — p. 7")).not.toHaveAttribute("href");
  });

  it("deduplicates citations and falls back to filename-only when page metadata is missing", () => {
    render(
      <ChatMessageDisplay
        msg={{
          type: "assistant",
          text: "Grounded answer",
          sources: [
            { filename: "alice-cheshire-cat-demo.pdf", page_number: 7 },
            { filename: "alice-cheshire-cat-demo.pdf", page_number: 7 },
            { filename: "policy.pdf" },
          ],
        }}
      />
    );

    expect(screen.getAllByText("alice-cheshire-cat-demo.pdf — p. 7")).toHaveLength(1);
    expect(screen.getByText("policy.pdf")).toBeInTheDocument();
    expect(screen.queryByText(/Section:/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Page:/i)).not.toBeInTheDocument();
  });

  it("moves legacy embedded sources out of the answer into the Sources card", () => {
    render(
      <ChatMessageDisplay
        msg={{
          type: "assistant",
          text: "The Cat disappears slowly.\n\n📚 Sources:\n- alice-cheshire-cat-demo.pdf",
          sources: [],
        }}
      />
    );

    expect(screen.getByText("The Cat disappears slowly.")).toBeInTheDocument();
    expect(screen.getByRole("region", { name: "Sources" })).toHaveTextContent(
      "alice-cheshire-cat-demo.pdf"
    );
    expect(screen.queryByText(/📚 Sources:/)).not.toBeInTheDocument();
  });
});
