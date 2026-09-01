import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useChatScroll } from "@/components/ChatSection/useChatScroll";

describe("useChatScroll", () => {
  let animationFrameCallback: FrameRequestCallback | undefined;

  beforeEach(() => {
    animationFrameCallback = undefined;
    vi.stubGlobal(
      "requestAnimationFrame",
      vi.fn((callback: FrameRequestCallback) => {
        animationFrameCallback = callback;
        return 1;
      })
    );
    vi.stubGlobal("cancelAnimationFrame", vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("uses a non-animated scroll while an assistant response is streaming", () => {
    const scrollIntoView = vi.fn();
    const { result } = renderHook(() => useChatScroll(["partial answer"], true));

    result.current.current = { scrollIntoView } as unknown as HTMLDivElement;

    expect(requestAnimationFrame).toHaveBeenCalledOnce();
    act(() => animationFrameCallback?.(0));

    expect(scrollIntoView).toHaveBeenCalledWith({ behavior: "auto", block: "end" });
  });

  it("cancels an obsolete scheduled scroll when streaming content changes", () => {
    const { rerender } = renderHook(({ history }) => useChatScroll(history, true), {
      initialProps: { history: ["first token"] },
    });

    rerender({ history: ["first token", "second token"] });

    expect(cancelAnimationFrame).toHaveBeenCalledWith(1);
    expect(requestAnimationFrame).toHaveBeenCalledTimes(2);
  });
});
