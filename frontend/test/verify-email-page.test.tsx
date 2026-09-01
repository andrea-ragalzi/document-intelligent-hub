import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import VerifyEmailPage from "@/app/verify-email/page";

const mocks = vi.hoisted(() => ({
  auth: {
    emailVerified: false,
    loading: false,
    logout: vi.fn(),
    refreshEmailVerification: vi.fn(),
    sendVerificationEmail: vi.fn(),
    user: { email: "recruiter@example.com" },
  },
  register: vi.fn(),
  replace: vi.fn(),
}));

vi.mock("@/contexts/AuthContext", () => ({
  useAuth: () => mocks.auth,
}));

vi.mock("@/hooks/useRegistration", () => ({
  useRegistration: () => ({ error: null, register: mocks.register }),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: mocks.replace }),
  useSearchParams: () => new URLSearchParams(),
}));

describe("VerifyEmailPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.auth.refreshEmailVerification.mockResolvedValue(false);
    mocks.register.mockResolvedValue("FREE");
  });

  it("does not activate FREE registration until Firebase confirms the email is verified", async () => {
    render(<VerifyEmailPage />);
    fireEvent.click(screen.getByRole("button", { name: /i.?ve verified/i }));

    await waitFor(() => {
      expect(mocks.auth.refreshEmailVerification).toHaveBeenCalledOnce();
      expect(mocks.register).not.toHaveBeenCalled();
      expect(screen.getByText(/not verified yet/i)).toBeInTheDocument();
    });
  });

  it("activates FREE registration and opens the dashboard only after a refreshed verified status", async () => {
    mocks.auth.refreshEmailVerification.mockResolvedValue(true);
    render(<VerifyEmailPage />);
    fireEvent.click(screen.getByRole("button", { name: /i.?ve verified/i }));

    await waitFor(() => {
      expect(mocks.register).toHaveBeenCalledOnce();
      expect(mocks.replace).toHaveBeenCalledWith("/dashboard");
    });
  });
});
