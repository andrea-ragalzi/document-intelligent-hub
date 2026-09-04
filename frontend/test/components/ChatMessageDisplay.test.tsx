import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ChatMessageDisplay } from "@/components/ChatMessageDisplay";

const getIdToken = vi.fn();
const openWindow = vi.fn();
const createObjectURL = vi.fn();
const revokeObjectURL = vi.fn();

vi.mock("@/contexts/AuthContext", () => ({
  useAuth: () => ({ getIdToken }),
}));

describe("ChatMessageDisplay sources", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    getIdToken.mockResolvedValue("firebase-token");
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(new Blob(["%PDF-1.4"]))));
    Object.defineProperty(URL, "createObjectURL", { value: createObjectURL, writable: true });
    Object.defineProperty(URL, "revokeObjectURL", { value: revokeObjectURL, writable: true });
    createObjectURL.mockReturnValue("blob:private-document");
    openWindow.mockReturnValue({ location: { href: "" }, close: vi.fn(), opener: null });
    vi.stubGlobal("open", openWindow);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

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

  it("fetches a private PDF with Firebase auth and opens the cited page", async () => {
    render(
      <ChatMessageDisplay
        msg={{
          type: "assistant",
          text: "Grounded answer",
          sources: [{ filename: "alice-demo.pdf", page_number: 7 }],
        }}
      />
    );

    fireEvent.click(screen.getByRole("button", { name: "alice-demo.pdf — p. 7" }));

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining("/documents/content?filename=alice-demo.pdf"),
        { headers: { Authorization: "Bearer firebase-token" } }
      );
    });
    expect(openWindow).toHaveBeenCalledWith("about:blank", "_blank");
    expect(openWindow.mock.results[0].value.location.href).toBe("blob:private-document#page=7");
  });

  it("opens filename-only citations at page one", async () => {
    render(
      <ChatMessageDisplay
        msg={{ type: "assistant", text: "Grounded answer", sources: [{ filename: "policy.pdf" }] }}
      />
    );

    fireEvent.click(screen.getByRole("button", { name: "policy.pdf" }));

    await waitFor(() => {
      expect(openWindow.mock.results[0].value.location.href).toBe("blob:private-document#page=1");
    });
  });

  it("keeps the PDF private and shows an error when authenticated fetch fails", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(null, { status: 404 })));
    render(
      <ChatMessageDisplay
        msg={{ type: "assistant", text: "Grounded answer", sources: [{ filename: "deleted.pdf" }] }}
      />
    );

    fireEvent.click(screen.getByRole("button", { name: "deleted.pdf" }));

    expect(screen.queryByRole("link", { name: "deleted.pdf" })).not.toBeInTheDocument();
    expect(openWindow).toHaveBeenCalledWith("about:blank", "_blank");
    expect(await screen.findByRole("alert")).toHaveTextContent("Unable to open this document.");
  });
});
