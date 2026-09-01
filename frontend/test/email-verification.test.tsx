import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { createElement, useState } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { AuthProvider, useAuth } from "@/contexts/AuthContext";
import { EmailVerificationCard } from "@/components/EmailVerificationCard";

const firebaseMocks = vi.hoisted(() => ({
  createUserWithEmailAndPassword: vi.fn(),
  getAuth: vi.fn(() => ({})),
  onAuthStateChanged: vi.fn(),
  sendEmailVerification: vi.fn(),
  signInWithEmailAndPassword: vi.fn(),
  signInWithPopup: vi.fn(),
  signOut: vi.fn(),
}));

vi.mock("@/lib/firebase", () => ({
  getFirebaseAuth: firebaseMocks.getAuth,
}));

vi.mock("firebase/auth", () => ({
  GoogleAuthProvider: class GoogleAuthProvider {},
  createUserWithEmailAndPassword: firebaseMocks.createUserWithEmailAndPassword,
  onAuthStateChanged: firebaseMocks.onAuthStateChanged,
  sendEmailVerification: firebaseMocks.sendEmailVerification,
  signInWithEmailAndPassword: firebaseMocks.signInWithEmailAndPassword,
  signInWithPopup: firebaseMocks.signInWithPopup,
  signOut: firebaseMocks.signOut,
}));

const user = {
  uid: "verification-user",
  email: "recruiter@example.com",
  emailVerified: false,
  getIdToken: vi.fn().mockResolvedValue("fresh-token"),
  reload: vi.fn(),
};

function SignUpTrigger() {
  const { signUp } = useAuth();
  return <button onClick={() => void signUp("recruiter@example.com", "password")}>Sign up</button>;
}

function VerificationRefreshTrigger() {
  const { refreshEmailVerification } = useAuth();
  const [verified, setVerified] = useState<boolean | null>(null);

  return (
    <>
      <button onClick={() => void refreshEmailVerification().then(setVerified)}>
        Refresh status
      </button>
      <output>{String(verified)}</output>
    </>
  );
}

describe("email verification lifecycle", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    user.emailVerified = false;
    user.reload.mockResolvedValue(undefined);
    user.getIdToken.mockResolvedValue("fresh-token");
    firebaseMocks.onAuthStateChanged.mockImplementation((_auth, callback) => {
      callback(null);
      return vi.fn();
    });
    firebaseMocks.createUserWithEmailAndPassword.mockResolvedValue({ user });
    firebaseMocks.sendEmailVerification.mockResolvedValue(undefined);
  });

  it("sends a Firebase verification email immediately after creating an email/password account", async () => {
    render(createElement(AuthProvider, null, createElement(SignUpTrigger)));

    fireEvent.click(screen.getByRole("button", { name: "Sign up" }));

    await waitFor(() => {
      expect(firebaseMocks.sendEmailVerification).toHaveBeenCalledWith(user);
    });
  });

  it("reloads the Firebase user and force-refreshes the ID token before reporting verification", async () => {
    firebaseMocks.onAuthStateChanged.mockImplementation((_auth, callback) => {
      callback(user);
      return vi.fn();
    });
    user.reload.mockImplementation(async () => {
      user.emailVerified = true;
    });

    render(createElement(AuthProvider, null, createElement(VerificationRefreshTrigger)));
    fireEvent.click(screen.getByRole("button", { name: "Refresh status" }));

    await waitFor(() => {
      expect(user.reload).toHaveBeenCalledOnce();
      expect(user.getIdToken).toHaveBeenCalledWith(true);
      expect(screen.getByText("true")).toBeInTheDocument();
    });
  });

  it("shows the email address and supports resending verification", async () => {
    const onResend = vi.fn().mockResolvedValue(undefined);
    const onCheck = vi.fn().mockResolvedValue(false);

    render(
      <EmailVerificationCard email="recruiter@example.com" onResend={onResend} onCheck={onCheck} />
    );

    expect(screen.getByText("recruiter@example.com")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /resend verification email/i }));

    await waitFor(() => expect(onResend).toHaveBeenCalledOnce());
  });

  it("reports that verification is still pending when the refreshed Firebase user is unverified", async () => {
    const onCheck = vi.fn().mockResolvedValue(false);

    render(
      <EmailVerificationCard email="recruiter@example.com" onResend={vi.fn()} onCheck={onCheck} />
    );

    fireEvent.click(screen.getByRole("button", { name: /i.?ve verified/i }));

    await waitFor(() => {
      expect(onCheck).toHaveBeenCalledOnce();
      expect(screen.getByText(/not verified yet/i)).toBeInTheDocument();
    });
  });
});
