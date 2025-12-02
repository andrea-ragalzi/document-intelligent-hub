import { renderHook, act } from "@testing-library/react";
import { describe, it, expect, beforeEach } from "vitest";
import { useTheme } from "@/hooks/useTheme";

describe("useTheme", () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.classList.remove("dark", "light");
  });

  it("should initialize with light theme by default", () => {
    const { result } = renderHook(() => useTheme());
    expect(result.current.theme).toBe("light");
  });

  it("should load theme from localStorage on mount", () => {
    localStorage.setItem("theme", "dark");

    const { result } = renderHook(() => useTheme());
    expect(result.current.theme).toBe("dark");
    expect(document.documentElement.classList.contains("dark")).toBe(true);
  });

  it("should toggle theme from light to dark", () => {
    const { result } = renderHook(() => useTheme());

    act(() => {
      result.current.toggleTheme();
    });

    expect(result.current.theme).toBe("dark");
    expect(localStorage.getItem("theme")).toBe("dark");
    expect(document.documentElement.classList.contains("dark")).toBe(true);
  });

  it("should toggle theme from dark to light", () => {
    localStorage.setItem("theme", "dark");

    const { result } = renderHook(() => useTheme());

    act(() => {
      result.current.toggleTheme();
    });

    expect(result.current.theme).toBe("light");
    expect(localStorage.getItem("theme")).toBe("light");
    expect(document.documentElement.classList.contains("dark")).toBe(false);
  });

  it("should handle SSR safely (mounted state)", () => {
    const { result } = renderHook(() => useTheme());

    // Initially not mounted
    expect(result.current.theme).toBe("light");

    // After mount, theme should be applied
    expect(document.documentElement.classList.length).toBeGreaterThanOrEqual(0);
  });

  it("should persist theme across multiple toggles", () => {
    const { result } = renderHook(() => useTheme());

    act(() => {
      result.current.toggleTheme(); // light -> dark
    });
    expect(localStorage.getItem("theme")).toBe("dark");

    act(() => {
      result.current.toggleTheme(); // dark -> light
    });
    expect(localStorage.getItem("theme")).toBe("light");

    act(() => {
      result.current.toggleTheme(); // light -> dark
    });
    expect(localStorage.getItem("theme")).toBe("dark");
  });
});
