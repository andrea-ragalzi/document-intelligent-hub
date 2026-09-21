import { act, renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { useDocumentStatus } from "@/hooks/useDocumentStatus";
import * as AuthContext from "@/contexts/AuthContext";

vi.mock("@/contexts/AuthContext", () => ({
  useAuth: vi.fn(),
}));

globalThis.fetch = vi.fn();

describe("useDocumentStatus", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(AuthContext.useAuth).mockReturnValue({
      user: { uid: "test-user-123" } as any,
      loading: false,
      getIdToken: vi.fn().mockResolvedValue("mock-token"),
    } as any);
  });

  it("keeps a newer post-seed result when the initial request finishes later", async () => {
    let resolveInitial!: (response: Response) => void;
    let resolvePostSeed!: (response: Response) => void;
    vi.mocked(fetch)
      .mockReturnValueOnce(
        new Promise<Response>(resolve => {
          resolveInitial = resolve;
        })
      )
      .mockReturnValueOnce(
        new Promise<Response>(resolve => {
          resolvePostSeed = resolve;
        })
      );

    const { result } = renderHook(() => useDocumentStatus("test-user-123"));
    await waitFor(() => expect(fetch).toHaveBeenCalledOnce());

    let postSeedRefresh!: Promise<boolean>;
    act(() => {
      postSeedRefresh = result.current.refreshDocumentStatus();
    });

    await act(async () => {
      resolvePostSeed(
        new Response(JSON.stringify({ has_documents: true, document_count: 1 }), {
          status: 200,
          headers: { "content-type": "application/json" },
        })
      );
      await postSeedRefresh;
    });

    await act(async () => {
      resolveInitial(
        new Response(JSON.stringify({ has_documents: false, document_count: 0 }), {
          status: 200,
          headers: { "content-type": "application/json" },
        })
      );
      await Promise.resolve();
    });

    expect(result.current.hasDocuments).toBe(true);
    expect(result.current.documentCount).toBe(1);
  });
});
