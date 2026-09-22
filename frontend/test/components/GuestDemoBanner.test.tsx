import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { GuestDemoBanner } from "@/components/GuestDemoBanner";

describe("GuestDemoBanner", () => {
  it("shows authoritative remaining queries and private-document CTAs", () => {
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

    expect(screen.getByText("Demo workspace")).toBeInTheDocument();
    expect(screen.getByText("5 questions remaining today")).toBeInTheDocument();
    expect(
      screen.getByText(/5 preloaded synthetic InGen documents inspired by Jurassic Park/i)
    ).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "View demo documents" }));
    fireEvent.click(screen.getByRole("button", { name: "Sign in" }));
    fireEvent.click(screen.getByRole("button", { name: "Create account" }));
    expect(onViewDocuments).toHaveBeenCalledOnce();
    expect(onSignIn).toHaveBeenCalledOnce();
    expect(onCreateAccount).toHaveBeenCalledOnce();
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

  it("collapses to a compact persistent row with all essential actions", () => {
    render(
      <GuestDemoBanner
        remaining={4}
        isLoading={false}
        onViewDocuments={vi.fn()}
        onSignIn={vi.fn()}
        onCreateAccount={vi.fn()}
      />
    );

    fireEvent.click(screen.getByRole("button", { name: "Minimize demo information" }));

    expect(
      screen.queryByText(/5 preloaded synthetic InGen documents inspired by Jurassic Park/i)
    ).not.toBeInTheDocument();
    expect(screen.getByText("Demo workspace")).toBeInTheDocument();
    expect(screen.getByText("4 questions remaining today")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "View demo documents" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Sign in" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Create account" })).toBeInTheDocument();
  });
});
