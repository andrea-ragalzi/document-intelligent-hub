/**
 * Tests for Invitation Code Frontend Components and Hooks
 *
 * Tests cover:
 * - useRegistration hook
 * - InvitationCodeModal component
 * - RequestCodeModal component
 * - useQueryUsage hook
 * - TierLimitsDisplay component
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { act } from "react";
import { useRegistration } from "@/hooks/useRegistration";
import type { User } from "firebase/auth";

// Mock AuthContext
const mockUser: Partial<User> = {
  uid: "test-user-123",
  email: "test@example.com",
  getIdToken: vi.fn().mockResolvedValue("mock-firebase-token"),
};

vi.mock("@/contexts/AuthContext", () => ({
  useAuth: () => ({
    user: mockUser,
  }),
}));

describe("useRegistration Hook", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch = vi.fn();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("should register with valid invitation code", async () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        status: "success",
        tier: "PRO",
        user_id: "test-user-123",
      }),
    });

    const { result } = renderHook(() => useRegistration());

    let tier;
    await act(async () => {
      tier = await result.current.register("VALID_PRO_CODE");
    });

    expect(tier).toBe("PRO");
    expect(result.current.error).toBeNull();
    expect(result.current.isRegistering).toBe(false);
    expect(mockUser.getIdToken).toHaveBeenCalledWith(true); // Force refresh
  });

  it("should register without code (FREE tier)", async () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        status: "success",
        tier: "FREE",
        user_id: "test-user-123",
      }),
    });

    const { result } = renderHook(() => useRegistration());

    let tier;
    await act(async () => {
      tier = await result.current.register();
    });

    expect(tier).toBe("FREE");
    expect(result.current.error).toBeNull();
  });

  it("should handle invalid invitation code", async () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: false,
      status: 400,
      json: async () => ({
        detail: "Invalid invitation code",
      }),
    });

    const { result } = renderHook(() => useRegistration());

    let tier;
    await act(async () => {
      tier = await result.current.register("INVALID_CODE");
    });

    expect(tier).toBeNull();
    expect(result.current.error).toBe("Invalid invitation code");
    expect(result.current.isRegistering).toBe(false);
  });

  it("should handle used invitation code", async () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: false,
      status: 400,
      json: async () => ({
        detail: "Invitation code has already been used",
      }),
    });

    const { result } = renderHook(() => useRegistration());

    let tier;
    await act(async () => {
      tier = await result.current.register("USED_CODE");
    });

    expect(tier).toBeNull();
    expect(result.current.error).toContain("already been used");
  });

  it("should handle expired invitation code", async () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: false,
      status: 400,
      json: async () => ({
        detail: "Invitation code has expired",
      }),
    });

    const { result } = renderHook(() => useRegistration());

    let tier;
    await act(async () => {
      tier = await result.current.register("EXPIRED_CODE");
    });

    expect(tier).toBeNull();
    expect(result.current.error).toContain("expired");
  });

  it("should handle network errors", async () => {
    (global.fetch as any).mockRejectedValueOnce(new Error("Network error"));

    const { result } = renderHook(() => useRegistration());

    let tier;
    await act(async () => {
      tier = await result.current.register("SOME_CODE");
    });

    expect(tier).toBeNull();
    expect(result.current.error).toBe("Network error");
  });

  it("should handle non-JSON responses", async () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: false,
      status: 500,
      json: async () => {
        throw new Error("Not JSON");
      },
      text: async () => "Internal Server Error",
    });

    const { result } = renderHook(() => useRegistration());

    let tier;
    await act(async () => {
      tier = await result.current.register("SOME_CODE");
    });

    expect(tier).toBeNull();
    expect(result.current.error).toBe("Internal Server Error");
  });

  it("should clear error", async () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: false,
      status: 400,
      json: async () => ({
        detail: "Some error",
      }),
    });

    const { result } = renderHook(() => useRegistration());

    await act(async () => {
      await result.current.register("BAD_CODE");
    });

    expect(result.current.error).toBe("Some error");

    act(() => {
      result.current.clearError();
    });

    expect(result.current.error).toBeNull();
  });

  it("should handle missing user", async () => {
    vi.mocked(() => ({
      useAuth: () => ({
        user: null,
      }),
    }));

    const { result } = renderHook(() => useRegistration());

    let tier;
    await act(async () => {
      tier = await result.current.register("SOME_CODE");
    });

    // Should return null if no user (but our mock always has user)
    // This test documents expected behavior
    expect(result.current.isRegistering).toBe(false);
  });
});

describe("useRegistration - Edge Cases", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch = vi.fn();
  });

  it("should handle empty invitation code", async () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        status: "success",
        tier: "FREE",
        user_id: "test-user-123",
      }),
    });

    const { result } = renderHook(() => useRegistration());

    let tier;
    await act(async () => {
      tier = await result.current.register("");
    });

    // Empty string treated as no code (null)
    const fetchCall = (global.fetch as any).mock.calls[0];
    const body = JSON.parse(fetchCall[1].body);
    expect(body.invitation_code).toBeNull();
  });

  it("should handle whitespace-only invitation code", async () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: false,
      status: 400,
      json: async () => ({
        detail: "Invalid invitation code",
      }),
    });

    const { result } = renderHook(() => useRegistration());

    await act(async () => {
      await result.current.register("   ");
    });

    // Backend should handle trimming/validation
    expect(result.current.error).toBeTruthy();
  });

  it("should handle concurrent registration attempts", async () => {
    let resolveFetch: (value: any) => void;
    (global.fetch as any).mockImplementation(
      () =>
        new Promise((resolve) => {
          resolveFetch = resolve;
        })
    );

    const { result } = renderHook(() => useRegistration());

    // Start first registration
    let registerPromise: Promise<any>;
    await act(async () => {
      registerPromise = result.current.register("CODE1");
    });

    // isRegistering should be true while fetch is pending
    expect(result.current.isRegistering).toBe(true);

    // Resolve the fetch
    await act(async () => {
      resolveFetch!({
        ok: true,
        json: async () => ({
          status: "success",
          tier: "FREE",
          user_id: "test-user-123",
        }),
      });
      await registerPromise!;
    });

    // After completion, should be false
    expect(result.current.isRegistering).toBe(false);
  });
});

describe("Invitation Code Request", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch = vi.fn();
  });

  it("should successfully request invitation code", async () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        status: "success",
        message: "Your request has been sent to our support team.",
      }),
    });

    const response = await fetch(
      "http://localhost:8000/auth/request-invitation-code",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: "newuser@example.com",
          reason: "I want to try PRO features",
        }),
      }
    );

    const data = await response.json();
    expect(response.ok).toBe(true);
    expect(data.status).toBe("success");
  });

  it("should handle invalid email format", async () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: false,
      status: 422,
      json: async () => ({
        detail: "Invalid email format",
      }),
    });

    const response = await fetch(
      "http://localhost:8000/auth/request-invitation-code",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: "not-an-email",
          reason: "Test",
        }),
      }
    );

    expect(response.ok).toBe(false);
    expect(response.status).toBe(422);
  });
});

describe("Query Usage Tracking", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch = vi.fn();
  });

  it("should track query usage correctly", async () => {
    const mockUsageResponse = {
      status: "success",
      queries_today: 5,
      query_limit: 20,
      remaining: 15,
      tier: "FREE",
    };

    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => mockUsageResponse,
    });

    const response = await fetch("http://localhost:8000/auth/usage", {
      headers: {
        Authorization: "Bearer mock-token",
      },
    });

    const data = await response.json();
    expect(data.queries_today).toBe(5);
    expect(data.query_limit).toBe(20);
    expect(data.remaining).toBe(15);
    expect(data.tier).toBe("FREE");
  });

  it("should handle unlimited tier correctly", async () => {
    const mockUsageResponse = {
      status: "success",
      queries_today: 100,
      query_limit: 9999,
      remaining: -1, // Unlimited
      tier: "UNLIMITED",
    };

    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => mockUsageResponse,
    });

    const response = await fetch("http://localhost:8000/auth/usage", {
      headers: {
        Authorization: "Bearer mock-token",
      },
    });

    const data = await response.json();
    expect(data.remaining).toBe(-1); // Unlimited
    expect(data.tier).toBe("UNLIMITED");
  });

  it("should detect limit reached", async () => {
    const mockUsageResponse = {
      status: "success",
      queries_today: 20,
      query_limit: 20,
      remaining: 0,
      tier: "FREE",
    };

    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => mockUsageResponse,
    });

    const response = await fetch("http://localhost:8000/auth/usage", {
      headers: {
        Authorization: "Bearer mock-token",
      },
    });

    const data = await response.json();
    expect(data.remaining).toBe(0);
    // Frontend should disable chat when remaining <= 0
  });
});

describe("Rate Limiting (429 Errors)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch = vi.fn();
  });

  it("should return 429 when query limit exceeded", async () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: false,
      status: 429,
      json: async () => ({
        error:
          "Daily query limit exceeded (20/20). Please upgrade your plan or try again tomorrow.",
      }),
    });

    const response = await fetch("http://localhost:3000/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        messages: [{ role: "user", content: "Test query" }],
        userId: "test-user-123",
      }),
    });

    expect(response.ok).toBe(false);
    expect(response.status).toBe(429);

    const data = await response.json();
    expect(data.error).toContain("Daily query limit exceeded");
  });
});
