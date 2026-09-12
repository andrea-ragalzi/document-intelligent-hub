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

function GoogleSignInTrigger() {
  const { signInWithGoogle } = useAuth();
  return <button onClick={() => void signInWithGoogle()}>Google sign in</button>;
}

function AuthStateObserver() {
  const { loading, logout, user } = useAuth();
  return (
    <>
      <output>{loading ? "loading" : user?.uid || "signed-out"}</output>
      <button onClick={() => void logout()}>Sign out</button>
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
    firebaseMocks.signInWithPopup.mockResolvedValue({ user });
    firebaseMocks.signOut.mockResolvedValue(undefined);
  });

  it("uses the popup flow on desktop browsers", async () => {
    Object.defineProperty(window.navigator, "userAgent", {
      configurable: true,
      value: "Mozilla/5.0 (X11; Linux x86_64) Chrome/120",
    });
    render(createElement(AuthProvider, null, createElement(GoogleSignInTrigger)));

    fireEvent.click(screen.getByRole("button", { name: "Google sign in" }));

    await waitFor(() => expect(firebaseMocks.signInWithPopup).toHaveBeenCalledOnce());
  });

  it("uses the popup flow on mobile when redirect helpers are not same-origin", async () => {
    Object.defineProperty(window.navigator, "userAgent", {
      configurable: true,
      value: "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) Safari/605.1",
    });
    render(createElement(AuthProvider, null, createElement(GoogleSignInTrigger)));

    fireEvent.click(screen.getByRole("button", { name: "Google sign in" }));

    await waitFor(() => expect(firebaseMocks.signInWithPopup).toHaveBeenCalledOnce());
  });

  it("restores Firebase auth state and clears user-scoped state after logout", async () => {
    firebaseMocks.onAuthStateChanged.mockImplementation((_auth, callback) => {
      callback(user);
      return vi.fn();
    });
    localStorage.setItem("rag_conversations", "previous-user-data");
    render(createElement(AuthProvider, null, createElement(AuthStateObserver)));

    expect(await screen.findByText("verification-user")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Sign out" }));

    await waitFor(() => {
      expect(firebaseMocks.signOut).toHaveBeenCalledOnce();
      expect(screen.getByText("signed-out")).toBeInTheDocument();
      expect(localStorage.getItem("rag_conversations")).toBeNull();
    });
  });

  it("unsubscribes the auth state listener when the provider unmounts", () => {
    const unsubscribe = vi.fn();
    firebaseMocks.onAuthStateChanged.mockReturnValue(unsubscribe);

    const view = render(createElement(AuthProvider, null, createElement("div")));
    view.unmount();

    expect(unsubscribe).toHaveBeenCalledOnce();
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
