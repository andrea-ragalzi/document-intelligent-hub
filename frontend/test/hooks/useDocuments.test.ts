import { renderHook, act, waitFor } from "@testing-library/react";
import { describe, it, expect, beforeEach, vi, afterEach } from "vitest";
import { useDocuments } from "@/hooks/useDocuments";
import * as AuthContext from "@/contexts/AuthContext";

// Mock AuthContext
vi.mock("@/contexts/AuthContext", () => ({
  useAuth: vi.fn(),
}));

// Mock fetch
globalThis.fetch = vi.fn();

describe("useDocuments", () => {
  const mockUserId = "test-user-123";
  const mockDocuments = [
    {
      filename: "document1.pdf",
      chunks_count: 10,
      language: "en",
      uploaded_at: "2024-01-01T00:00:00Z",
    },
    {
      filename: "document2.pdf",
      chunks_count: 5,
      language: "it",
      uploaded_at: "2024-01-02T00:00:00Z",
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();

    // Mock useAuth to return getIdToken function
    vi.mocked(AuthContext.useAuth).mockReturnValue({
      user: { uid: mockUserId } as any,
      loading: false,
      getIdToken: vi.fn().mockResolvedValue("mock-token"),
    } as any);

    // Mock successful fetch by default
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        documents: mockDocuments,
        total_count: 2,
        user_id: mockUserId,
      }),
    } as Response);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("should initialize with loading state", () => {
    const { result } = renderHook(() => useDocuments(mockUserId));
    expect(result.current.isLoading).toBe(true);
    expect(result.current.documents).toEqual([]);
    expect(result.current.error).toBeNull();
  });

  it("should load documents on mount", async () => {
    const { result } = renderHook(() => useDocuments(mockUserId));

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.documents).toEqual(mockDocuments);
    expect(result.current.error).toBeNull();
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining(`/documents/list?user_id=${mockUserId}`),
      expect.objectContaining({
        cache: "no-store",
        headers: expect.objectContaining({
          "Cache-Control": "no-cache",
        }),
      })
    );
  });

  it("should handle fetch error gracefully", async () => {
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: false,
      status: 500,
      statusText: "Internal Server Error",
    } as Response);

    const { result } = renderHook(() => useDocuments(mockUserId));

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.documents).toEqual([]);
    expect(result.current.error).toContain("Failed to fetch documents");
  });

  it("should not load documents when userId is null", async () => {
    const { result } = renderHook(() => useDocuments(null));

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.documents).toEqual([]);
    expect(fetch).not.toHaveBeenCalled();
  });

  it("should refresh documents manually", async () => {
    const { result } = renderHook(() => useDocuments(mockUserId));

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // Clear previous calls
    vi.clearAllMocks();

    // Manually refresh
    await act(async () => {
      await result.current.refreshDocuments();
    });

    expect(fetch).toHaveBeenCalledTimes(1);
    expect(result.current.documents).toEqual(mockDocuments);
  });

  it("should delete a document", async () => {
    const { result } = renderHook(() => useDocuments(mockUserId));

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // Mock delete response
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        message: "Document deleted",
        filename: "document1.pdf",
        chunks_deleted: 10,
      }),
    } as Response);

    // Mock updated list response
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        documents: [mockDocuments[1]], // Only second document remains
        total_count: 1,
        user_id: mockUserId,
      }),
    } as Response);

    await act(async () => {
      await result.current.deleteDocument("document1.pdf");
    });

    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining("/documents/delete"),
      expect.objectContaining({ method: "DELETE" })
    );

    await waitFor(() => {
      expect(result.current.documents).toHaveLength(1);
      expect(result.current.documents[0].filename).toBe("document2.pdf");
    });
  });

  it("should handle delete error", async () => {
    const { result } = renderHook(() => useDocuments(mockUserId));

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // Mock delete error
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: false,
      status: 404,
      statusText: "Not Found",
      json: async () => ({ detail: "Document not found" }),
    } as Response);

    await expect(
      act(async () => {
        await result.current.deleteDocument("nonexistent.pdf");
      })
    ).rejects.toThrow("Document not found");
  });

  it("should delete all documents", async () => {
    const { result } = renderHook(() => useDocuments(mockUserId));

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // Mock delete all response
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        message: "All documents deleted",
        chunks_deleted: 15,
      }),
    } as Response);

    // Mock empty list response
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        documents: [],
        total_count: 0,
        user_id: mockUserId,
      }),
    } as Response);

    await act(async () => {
      await result.current.deleteAllDocuments();
    });

    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining("/documents/delete-all"),
      expect.objectContaining({ method: "DELETE" })
    );

    await waitFor(() => {
      expect(result.current.documents).toHaveLength(0);
    });
  });

  it("should throw error when deleting without userId", async () => {
    const { result } = renderHook(() => useDocuments(null));

    await expect(
      act(async () => {
        await result.current.deleteDocument("test.pdf");
      })
    ).rejects.toThrow("User ID is required");
  });

  // NOTE: Test removed - 'documentUploaded' event listener was removed from implementation
  // to prevent multiple refreshes. DocumentManager now handles refresh after upload directly.

  it("should dispatch refreshDocumentStatus event after delete", async () => {
    const { result } = renderHook(() => useDocuments(mockUserId));

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    const eventListener = vi.fn();
    window.addEventListener("refreshDocumentStatus", eventListener);

    // Mock delete response
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        message: "Document deleted",
        filename: "document1.pdf",
        chunks_deleted: 10,
      }),
    } as Response);

    // Mock list response
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        documents: [],
        total_count: 0,
        user_id: mockUserId,
      }),
    } as Response);

    await act(async () => {
      await result.current.deleteDocument("document1.pdf");
    });

    expect(eventListener).toHaveBeenCalled();

    window.removeEventListener("refreshDocumentStatus", eventListener);
  });

  it("should reload documents when userId changes", async () => {
    const { result, rerender } = renderHook(
      ({ userId }) => useDocuments(userId),
      { initialProps: { userId: mockUserId } }
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    const initialCallCount = vi.mocked(fetch).mock.calls.length;

    // Change userId
    const newUserId = "different-user-456";
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        documents: [],
        total_count: 0,
        user_id: newUserId,
      }),
    } as Response);

    rerender({ userId: newUserId });

    await waitFor(() => {
      expect(vi.mocked(fetch).mock.calls.length).toBeGreaterThan(
        initialCallCount
      );
    });

    expect(fetch).toHaveBeenLastCalledWith(
      expect.stringContaining(`user_id=${newUserId}`),
      expect.objectContaining({
        cache: "no-store",
        headers: expect.objectContaining({
          "Cache-Control": "no-cache",
        }),
      })
    );
  });

  it("should handle network error", async () => {
    vi.mocked(fetch).mockRejectedValueOnce(new Error("Network error"));

    const { result } = renderHook(() => useDocuments(mockUserId));

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.documents).toEqual([]);
    expect(result.current.error).toBe("Network error");
  });
});
