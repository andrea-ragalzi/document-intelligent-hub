import { afterEach, describe, expect, it, vi } from "vitest";
import { POST } from "@/app/api/chat/route";

describe("POST /api/chat", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("preserves backend source citations as structured assistant annotations", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            answer: "Grounded answer",
            source_documents: ["alice-cheshire-cat-demo.pdf"],
            citations: [{ filename: "alice-cheshire-cat-demo.pdf", page_number: 7 }],
          }),
          { status: 200 }
        )
      )
    );

    const response = await POST(
      new Request("http://localhost/api/chat", {
        method: "POST",
        headers: { Authorization: "Bearer test-token", "Content-Type": "application/json" },
        body: JSON.stringify({
          userId: "user-a",
          messages: [{ role: "user", content: "What happens?" }],
        }),
      })
    );

    expect(await response.text()).toContain(
      '8:[{"type":"sources","sources":[{"filename":"alice-cheshire-cat-demo.pdf","page_number":7}]}]'
    );
  });

  it("sends only the most recent fourteen history messages to the backend", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ answer: "Grounded answer" }), { status: 200 })
    );
    vi.stubGlobal("fetch", fetchMock);
    const history = Array.from({ length: 16 }, (_, index) => ({
      role: index % 2 === 0 ? "user" : "assistant",
      content: `message-${index}`,
    }));

    await POST(
      new Request("http://localhost/api/chat", {
        method: "POST",
        headers: { Authorization: "Bearer test-token", "Content-Type": "application/json" },
        body: JSON.stringify({
          userId: "user-a",
          messages: [...history, { role: "user", content: "current question" }],
        }),
      })
    );

    const request = JSON.parse(String(fetchMock.mock.calls[0][1].body));
    expect(request.conversation_history).toHaveLength(14);
    expect(request.conversation_history[0].content).toBe("message-2");
    expect(request.conversation_history.at(-1).content).toBe("message-15");
  });
});
