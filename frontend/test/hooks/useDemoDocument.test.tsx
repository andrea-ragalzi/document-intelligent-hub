import { renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const getIdToken = vi.fn();

vi.mock("@/contexts/AuthContext", () => ({
  useAuth: () => ({ getIdToken }),
}));

import { useDemoDocument } from "@/hooks/useDemoDocument";

describe("useDemoDocument", () => {
  beforeEach(() => {
    getIdToken.mockReset();
    getIdToken.mockResolvedValue("firebase-token");
    vi.stubGlobal("fetch", vi.fn());
  });

  it("does not block the dashboard when demo seeding fails", async () => {
    vi.mocked(fetch).mockResolvedValue(new Response("unavailable", { status: 500 }));

    const { result } = renderHook(() => useDemoDocument({ userId: "user-a" }));

    await waitFor(() => expect(result.current.state).toBe("failed"));
    expect(fetch).toHaveBeenCalledTimes(2);
  });

  it("recovers from one transient seed failure and refreshes document state", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(new Response("unavailable", { status: 502 }))
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            status: "ready",
            filename: "alice-cheshire-cat-demo.pdf",
            suggested_questions: ["How is the Cheshire Cat described?"],
          }),
          { status: 200, headers: { "content-type": "application/json" } }
        )
      );
    const onReady = vi.fn();

    const { result } = renderHook(() => useDemoDocument({ userId: "user-a", onReady }));

    await waitFor(() => expect(result.current.state).toBe("ready"));
    expect(fetch).toHaveBeenCalledTimes(2);
    expect(onReady).toHaveBeenCalledOnce();
  });

  it("refreshes document state after the final seed failure", async () => {
    vi.mocked(fetch).mockResolvedValue(new Response("unavailable", { status: 502 }));
    const onReady = vi.fn();

    const { result } = renderHook(() => useDemoDocument({ userId: "user-a", onReady }));

    await waitFor(() => expect(result.current.state).toBe("failed"));
    expect(onReady).toHaveBeenCalledOnce();
  });

  it("seeds only once while the authenticated dashboard remains mounted", async () => {
    vi.mocked(fetch).mockResolvedValue(
      new Response(
        JSON.stringify({
          status: "seeded",
          filename: "alice-cheshire-cat-demo.pdf",
          suggested_questions: ["How is the Cheshire Cat described?"],
        }),
        { status: 200, headers: { "content-type": "application/json" } }
      )
    );

    const { result, rerender } = renderHook(() => useDemoDocument({ userId: "user-a" }));
    await waitFor(() => expect(result.current.state).toBe("ready"));
    rerender();

    expect(fetch).toHaveBeenCalledOnce();
    expect(result.current.suggestedQuestions).toEqual(["How is the Cheshire Cat described?"]);
  });
});
