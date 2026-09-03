import { useEffect, type RefObject } from "react";

/** Keep a full-screen app container within the browser's visible viewport on mobile. */
export const useVisualViewportHeight = (containerRef: RefObject<HTMLElement | null>) => {
  useEffect(() => {
    const viewport = window.visualViewport;
    if (!viewport) return undefined;

    const updateHeight = () => {
      containerRef.current?.style.setProperty("height", `${Math.round(viewport.height)}px`);
    };

    updateHeight();
    viewport.addEventListener("resize", updateHeight);
    viewport.addEventListener("scroll", updateHeight);

    return () => {
      viewport.removeEventListener("resize", updateHeight);
      viewport.removeEventListener("scroll", updateHeight);
      containerRef.current?.style.removeProperty("height");
    };
  }, [containerRef]);
};
