import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import SignupForm from "@/components/SignupForm";

const mocks = vi.hoisted(() => ({
  push: vi.fn(),
  replace: vi.fn(),
  signInWithGoogle: vi.fn(),
  signUp: vi.fn(),
}));

vi.mock("@/contexts/AuthContext", () => ({
  useAuth: () => ({
    signInWithGoogle: mocks.signInWithGoogle,
    signUp: mocks.signUp,
  }),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mocks.push, replace: mocks.replace }),
}));

describe("SignupForm verification handoff", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const submitValidForm = () => {
    fireEvent.change(screen.getByLabelText("Email"), {
      target: { value: "recruiter@example.com" },
    });
    fireEvent.change(screen.getByLabelText("Password"), { target: { value: "password" } });
    fireEvent.change(screen.getByLabelText("Confirm Password"), {
      target: { value: "password" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Sign Up" }));
  };

  it("sends a newly created email/password user to the verification page", async () => {
    mocks.signUp.mockResolvedValue({ verificationEmailSent: true });
    render(<SignupForm />);
    submitValidForm();

    await waitFor(() => {
      expect(mocks.signUp).toHaveBeenCalledWith("recruiter@example.com", "password");
      expect(mocks.replace).toHaveBeenCalledWith("/verify-email");
    });
  });

  it("still shows a recovery path when the initial verification email cannot be sent", async () => {
    mocks.signUp.mockResolvedValue({ verificationEmailSent: false });
    render(<SignupForm />);
    submitValidForm();

    await waitFor(() => {
      expect(mocks.replace).toHaveBeenCalledWith("/verify-email?delivery=failed");
    });
  });

  it("uses the same Google flow for first-time users and prevents duplicate submissions", async () => {
    let completeSignIn: (() => void) | undefined;
    mocks.signInWithGoogle.mockImplementation(
      () =>
        new Promise<void>(resolve => {
          completeSignIn = resolve;
        })
    );
    render(<SignupForm />);

    const googleButton = screen.getByRole("button", { name: "Sign up with Google" });
    fireEvent.click(googleButton);
    fireEvent.click(googleButton);

    expect(mocks.signInWithGoogle).toHaveBeenCalledOnce();
    expect(screen.getByRole("button", { name: "Signing up with Google..." })).toBeDisabled();
    completeSignIn?.();

    await waitFor(() => expect(mocks.push).toHaveBeenCalledWith("/"));
  });
});
