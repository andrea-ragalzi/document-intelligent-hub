import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import LoginForm from "@/components/LoginForm";

const mocks = vi.hoisted(() => ({
  push: vi.fn(),
  signIn: vi.fn(),
  signInWithGoogle: vi.fn(),
}));

vi.mock("@/contexts/AuthContext", () => ({
  useAuth: () => ({
    signIn: mocks.signIn,
    signInWithGoogle: mocks.signInWithGoogle,
  }),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mocks.push }),
}));

describe("LoginForm", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  function enterCredentials() {
    fireEvent.change(screen.getByLabelText("Email"), {
      target: { value: "user@example.com" },
    });
    fireEvent.change(screen.getByLabelText("Password"), {
      target: { value: "password" },
    });
  }

  it("prevents duplicate email sign-in submissions and navigates after success", async () => {
    let completeSignIn: (() => void) | undefined;
    mocks.signIn.mockImplementation(
      () =>
        new Promise<void>(resolve => {
          completeSignIn = resolve;
        })
    );
    render(<LoginForm />);
    enterCredentials();

    const submit = screen.getByRole("button", { name: "Sign In" });
    fireEvent.click(submit);
    fireEvent.click(submit);

    expect(mocks.signIn).toHaveBeenCalledOnce();
    expect(screen.getByRole("button", { name: "Signing in..." })).toBeDisabled();
    completeSignIn?.();

    await waitFor(() => expect(mocks.push).toHaveBeenCalledWith("/"));
  });

  it("shows a safe authentication error and clears it when the user retries", async () => {
    mocks.signIn.mockRejectedValueOnce(new Error("Incorrect email or password."));
    mocks.signIn.mockResolvedValueOnce(undefined);
    render(<LoginForm />);
    enterCredentials();

    fireEvent.click(screen.getByRole("button", { name: "Sign In" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Incorrect email or password.");

    fireEvent.click(screen.getByRole("button", { name: "Sign In" }));
    await waitFor(() => expect(screen.queryByRole("alert")).not.toBeInTheDocument());
  });

  it("prevents duplicate Google sign-in requests", async () => {
    let completeSignIn: (() => void) | undefined;
    mocks.signInWithGoogle.mockImplementation(
      () =>
        new Promise<void>(resolve => {
          completeSignIn = resolve;
        })
    );
    render(<LoginForm />);

    const googleButton = screen.getByRole("button", { name: "Sign in with Google" });
    fireEvent.click(googleButton);
    fireEvent.click(googleButton);

    expect(mocks.signInWithGoogle).toHaveBeenCalledOnce();
    expect(screen.getByRole("button", { name: "Signing in with Google..." })).toBeDisabled();
    completeSignIn?.();

    await waitFor(() => expect(mocks.push).toHaveBeenCalledWith("/"));
  });
});
