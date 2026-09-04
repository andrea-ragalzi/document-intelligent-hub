import { act, renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useChat } from "ai/react";
import { useAuth } from "@/contexts/AuthContext";
import { useChatAI } from "@/hooks/useChatAI";

vi.mock("ai/react", () => ({
  useChat: vi.fn(),
}));

vi.mock("@/contexts/AuthContext", () => ({
  useAuth: vi.fn(),
}));

describe("useChatAI", () => {
  const submitChat = vi.fn();
  const getIdToken = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();

    vi.mocked(useAuth).mockReturnValue({
      getIdToken,
    } as unknown as ReturnType<typeof useAuth>);
    vi.mocked(useChat).mockReturnValue({
      messages: [],
      input: "question",
      handleInputChange: vi.fn(),
      handleSubmit: submitChat,
      isLoading: false,
      error: undefined,
      setMessages: vi.fn(),
    } as unknown as ReturnType<typeof useChat>);
  });

  it("gets a current Firebase token for every chat submission", async () => {
    getIdToken.mockResolvedValueOnce("first-token").mockResolvedValueOnce("refreshed-token");
    const { result } = renderHook(() =>
      useChatAI({ userId: "user-a", selectedOutputLanguage: "it" })
    );

    await act(async () => {
      await result.current.handleSubmit({ preventDefault: vi.fn() });
      await result.current.handleSubmit({ preventDefault: vi.fn() });
    });

    expect(getIdToken).toHaveBeenCalledTimes(2);
    expect(submitChat).toHaveBeenNthCalledWith(1, undefined, {
      headers: { Authorization: "Bearer first-token" },
    });
    expect(submitChat).toHaveBeenNthCalledWith(2, undefined, {
      headers: { Authorization: "Bearer refreshed-token" },
    });
  });

  it("preserves source annotations on the matching assistant message", () => {
    vi.mocked(useChat).mockReturnValue({
      messages: [
        {
          id: "assistant-1",
          role: "assistant",
          content: "The answer is grounded in the document.",
          annotations: [
            { type: "sources", sources: ["alice-cheshire-cat-demo.pdf", "policy.pdf"] },
          ],
        },
      ],
      input: "",
      handleInputChange: vi.fn(),
      handleSubmit: submitChat,
      isLoading: false,
      error: undefined,
      setMessages: vi.fn(),
    } as unknown as ReturnType<typeof useChat>);

    const { result } = renderHook(() =>
      useChatAI({ userId: "user-a", selectedOutputLanguage: "en" })
    );

    expect(result.current.chatHistory).toEqual([
      {
        type: "assistant",
        text: "The answer is grounded in the document.",
        sources: [{ filename: "alice-cheshire-cat-demo.pdf" }, { filename: "policy.pdf" }],
      },
    ]);
  });
});
