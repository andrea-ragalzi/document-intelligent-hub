import { act, renderHook } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { useDocumentUpload } from "@/hooks/useDocumentUpload";

vi.mock("@/contexts/AuthContext", () => ({
  useAuth: () => ({ getIdToken: vi.fn().mockResolvedValue("firebase-token") }),
}));

describe("useDocumentUpload", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("does not ask an authenticated user to enter a UID", () => {
    const { result } = renderHook(() => useDocumentUpload());
    expect(result.current.uploadAlert.message).toBe("Select a PDF to upload.");
  });

  it("queues every selected PDF and uploads them one at a time", async () => {
    const first = new File(["first"], "first.pdf", { type: "application/pdf" });
    const second = new File(["second"], "second.pdf", { type: "application/pdf" });
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          status: "success",
          filename: "uploaded.pdf",
          chunks_indexed: 1,
          message: "Indexed",
        }),
        { status: 201 }
      )
    );
    vi.stubGlobal("fetch", fetchMock);

    const { result } = renderHook(() => useDocumentUpload());
    act(() => {
      result.current.handleFileChange({
        target: { files: [first, second] },
      } as unknown as React.ChangeEvent<HTMLInputElement>);
    });

    expect(result.current.files).toEqual([first, second]);

    await act(async () => {
      await result.current.handleUpload(
        { preventDefault: vi.fn() } as unknown as React.FormEvent,
        "owner-uid",
        []
      );
    });

    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(fetchMock.mock.calls[0][1].body.get("file").name).toBe("first.pdf");
    expect(fetchMock.mock.calls[1][1].body.get("file").name).toBe("second.pdf");
  });

  it("waits for a duplicate-file decision before making a request", async () => {
    const duplicate = new File(["replacement"], "report.pdf", {
      type: "application/pdf",
    });
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          status: "success",
          filename: "report (1).pdf",
          chunks_indexed: 1,
          message: "Indexed",
        }),
        { status: 201 }
      )
    );
    vi.stubGlobal("fetch", fetchMock);

    const { result } = renderHook(() => useDocumentUpload());
    act(() => {
      result.current.handleFileChange({
        target: { files: [duplicate] },
      } as unknown as React.ChangeEvent<HTMLInputElement>);
    });

    await act(async () => {
      await result.current.handleUpload(
        { preventDefault: vi.fn() } as unknown as React.FormEvent,
        "owner-uid",
        ["report.pdf"]
      );
    });

    expect(result.current.pendingDuplicate?.name).toBe("report.pdf");
    expect(fetchMock).not.toHaveBeenCalled();

    await act(async () => {
      await result.current.resolveDuplicate("rename");
    });

    expect(fetchMock).toHaveBeenCalledOnce();
    expect(fetchMock.mock.calls[0][1].body.get("duplicate_action")).toBe("rename");
  });
});
