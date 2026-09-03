import { afterEach, describe, expect, it, vi } from "vitest";
import { POST } from "@/app/api/chat/route";

describe("POST /api/chat", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("preserves backend source filenames as structured assistant annotations", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            answer: "Grounded answer",
            source_documents: ["alice-cheshire-cat-demo.pdf"],
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
      '8:[{"type":"sources","sources":["alice-cheshire-cat-demo.pdf"]}]'
    );
  });
});
