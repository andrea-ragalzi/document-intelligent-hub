import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { GuestDemoBanner } from "@/components/GuestDemoBanner";

describe("GuestDemoBanner", () => {
  it("shows authoritative remaining queries and private-document CTAs", () => {
    const onSignIn = vi.fn();
    const onCreateAccount = vi.fn();
    render(
      <GuestDemoBanner
        remaining={5}
        isLoading={false}
        onSignIn={onSignIn}
        onCreateAccount={onCreateAccount}
      />
    );

    expect(screen.getByText("Demo workspace")).toBeInTheDocument();
    expect(screen.getByText("5 questions remaining today")).toBeInTheDocument();
    expect(screen.getByText(/upload private documents/i)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Sign in" }));
    fireEvent.click(screen.getByRole("button", { name: "Create account" }));
    expect(onSignIn).toHaveBeenCalledOnce();
    expect(onCreateAccount).toHaveBeenCalledOnce();
  });

  it("uses singular wording for one remaining query", () => {
    render(
      <GuestDemoBanner
        remaining={1}
        isLoading={false}
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
        onSignIn={vi.fn()}
        onCreateAccount={vi.fn()}
      />
    );

    expect(screen.getByText("Unlimited in development")).toBeInTheDocument();
  });
});
