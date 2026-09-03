import { act, renderHook } from "@testing-library/react";
import type { RefObject } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useVisualViewportHeight } from "@/hooks/useVisualViewportHeight";

describe("useVisualViewportHeight", () => {
  const container = document.createElement("div");
  const containerRef: RefObject<HTMLDivElement | null> = { current: container };
  let resizeListener: EventListener | undefined;
  let scrollListener: EventListener | undefined;
  let visualViewport: {
    height: number;
    addEventListener: ReturnType<typeof vi.fn>;
    removeEventListener: ReturnType<typeof vi.fn>;
  };

  beforeEach(() => {
    container.removeAttribute("style");
    visualViewport = {
      height: 760,
      addEventListener: vi.fn((event: string, listener: EventListener) => {
        if (event === "resize") resizeListener = listener;
        if (event === "scroll") scrollListener = listener;
      }),
      removeEventListener: vi.fn(),
    };
    vi.stubGlobal("visualViewport", visualViewport);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("keeps the dashboard container aligned to the visual viewport", () => {
    const { unmount } = renderHook(() => useVisualViewportHeight(containerRef));

    expect(container.style.height).toBe("760px");
    expect(visualViewport.addEventListener).toHaveBeenCalledWith("resize", expect.any(Function));
    expect(visualViewport.addEventListener).toHaveBeenCalledWith("scroll", expect.any(Function));

    visualViewport.height = 420;
    act(() => resizeListener?.(new Event("resize")));
    expect(container.style.height).toBe("420px");

    visualViewport.height = 760;
    act(() => scrollListener?.(new Event("scroll")));
    expect(container.style.height).toBe("760px");

    unmount();
    expect(container.style.height).toBe("");
  });
});
