import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { GuestDemoBanner } from "@/components/GuestDemoBanner";

describe("GuestDemoBanner", () => {
  beforeEach(() => {
    sessionStorage.clear();
  });

  it("shows the mobile intro and document/auth actions", () => {
    const onSignIn = vi.fn();
    const onCreateAccount = vi.fn();
    const onViewDocuments = vi.fn();
    render(
      <GuestDemoBanner
        remaining={5}
        isLoading={false}
        onViewDocuments={onViewDocuments}
        onSignIn={onSignIn}
        onCreateAccount={onCreateAccount}
      />
    );

    expect(screen.getByText("You’re exploring the demo")).toBeInTheDocument();
    expect(screen.getByText(/5 preloaded InGen documents inspired by/i)).toBeInTheDocument();
    expect(screen.getByText("Jurassic Park")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "View documents" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Got it" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "View documents" }));
    expect(onViewDocuments).toHaveBeenCalledOnce();
  });

  it("uses singular wording for one remaining query", () => {
    render(
      <GuestDemoBanner
        remaining={1}
        isLoading={false}
        onViewDocuments={vi.fn()}
        onSignIn={vi.fn()}
        onCreateAccount={vi.fn()}
      />
    );

    expect(screen.getByText("1 question remaining today")).toBeInTheDocument();
  });

  it("shows an explicit unlimited development allowance", () => {
    render(
      <GuestDemoBanner
        remaining={null}
        limited={false}
        isLoading={false}
        onViewDocuments={vi.fn()}
        onSignIn={vi.fn()}
        onCreateAccount={vi.fn()}
      />
    );

    expect(screen.getByText("Unlimited in development")).toBeInTheDocument();
  });

  it("dismisses the intro and leaves only the compact demo bar", () => {
    render(
      <GuestDemoBanner
        remaining={4}
        isLoading={false}
        onViewDocuments={vi.fn()}
        onSignIn={vi.fn()}
        onCreateAccount={vi.fn()}
      />
    );

    fireEvent.click(screen.getByRole("button", { name: "Got it" }));

    expect(screen.queryByText("You’re exploring the demo")).not.toBeInTheDocument();
    expect(
      screen.queryByText(/5 preloaded InGen documents inspired by Jurassic Park/i)
    ).not.toBeInTheDocument();
    const mobileBanner = screen.getByTestId("mobile-demo-banner");
    expect(mobileBanner).not.toHaveTextContent("DEMO");
    expect(mobileBanner).not.toHaveTextContent("questions");
    expect(screen.getByRole("button", { name: "Documents" }).parentElement).toHaveClass(
      "justify-center"
    );
    expect(screen.getByRole("button", { name: "Documents" })).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: "Sign in" })).toHaveLength(2);
    expect(screen.getAllByRole("button", { name: "Create account" })).toHaveLength(2);
  });

  it("persists mobile intro dismissal for the current session", () => {
    const props = {
      remaining: 4,
      isLoading: false,
      onViewDocuments: vi.fn(),
      onSignIn: vi.fn(),
      onCreateAccount: vi.fn(),
    };
    const { unmount } = render(<GuestDemoBanner {...props} />);
    fireEvent.click(screen.getByRole("button", { name: "Got it" }));
    unmount();

    render(<GuestDemoBanner {...props} />);
    expect(screen.queryByText("You’re exploring the demo")).not.toBeInTheDocument();
    expect(screen.getByTestId("mobile-demo-banner")).toBeInTheDocument();
  });
});
