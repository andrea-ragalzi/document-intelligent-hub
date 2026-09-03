import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ChatMessageDisplay } from "@/components/ChatMessageDisplay";

describe("ChatMessageDisplay sources", () => {
  it("renders one filename in a compact Sources section", () => {
    render(
      <ChatMessageDisplay
        msg={{
          type: "assistant",
          text: "Grounded answer",
          sources: ["alice-cheshire-cat-demo.pdf"],
        }}
      />
    );

    expect(screen.getByText("Sources")).toBeInTheDocument();
    expect(screen.getByText("alice-cheshire-cat-demo.pdf")).not.toHaveAttribute("href");
  });

  it("renders multiple source filenames without adding unsupported metadata", () => {
    render(
      <ChatMessageDisplay
        msg={{
          type: "assistant",
          text: "Grounded answer",
          sources: ["alice-cheshire-cat-demo.pdf", "policy.pdf"],
        }}
      />
    );

    expect(screen.getByText("alice-cheshire-cat-demo.pdf")).toBeInTheDocument();
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
