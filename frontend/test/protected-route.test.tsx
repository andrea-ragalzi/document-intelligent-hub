import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import ProtectedRoute from "@/components/ProtectedRoute";

const mocks = vi.hoisted(() => ({
  auth: {
    emailVerified: false,
    loading: true,
    user: null as { uid: string } | null,
  },
  push: vi.fn(),
}));

vi.mock("@/contexts/AuthContext", () => ({
  useAuth: () => mocks.auth,
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mocks.push }),
}));

describe("ProtectedRoute authentication lifecycle", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.auth.emailVerified = false;
    mocks.auth.loading = true;
    mocks.auth.user = null;
  });

  it("does not expose protected content before Firebase restores auth state", () => {
    render(
      <ProtectedRoute>
        <div>Protected account data</div>
      </ProtectedRoute>
    );

    expect(screen.getByText("Loading...")).toBeInTheDocument();
    expect(screen.queryByText("Protected account data")).not.toBeInTheDocument();
    expect(mocks.push).not.toHaveBeenCalled();
  });

  it("redirects an unauthenticated user after initialization", async () => {
    mocks.auth.loading = false;
    render(
      <ProtectedRoute>
        <div>Protected account data</div>
      </ProtectedRoute>
    );

    await waitFor(() => expect(mocks.push).toHaveBeenCalledWith("/login"));
    expect(screen.queryByText("Protected account data")).not.toBeInTheDocument();
  });

  it("renders protected content for an authenticated verified user", () => {
    mocks.auth.loading = false;
    mocks.auth.emailVerified = true;
    mocks.auth.user = { uid: "verified-user" };

    render(
      <ProtectedRoute>
        <div>Protected account data</div>
      </ProtectedRoute>
    );

    expect(screen.getByText("Protected account data")).toBeInTheDocument();
    expect(mocks.push).not.toHaveBeenCalled();
  });
});
