import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import AboutPage from "@/app/about/page";
import LandingPage from "@/app/page";

const mocks = vi.hoisted(() => ({
  auth: { loading: false, user: null as { uid: string } | null },
  push: vi.fn(),
}));

vi.mock("@/contexts/AuthContext", () => ({
  useAuth: () => mocks.auth,
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mocks.push }),
}));

describe("public pages", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.auth.loading = false;
    mocks.auth.user = null;
  });

  it("presents the plain-language PDF value proposition and demo CTA", async () => {
    render(<LandingPage />);

    expect(await screen.findByText(/ask questions about your PDFs/i)).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { level: 1, name: /get answers from your documents/i })
    ).toBeInTheDocument();
    expect(screen.getByText(/ask questions in plain language/i)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /try the demo/i }));
    expect(mocks.push).toHaveBeenCalledWith("/signup");

    const githubLink = screen.getByRole("link", { name: /view github/i });
    expect(githubLink).toHaveAttribute(
      "href",
      "https://github.com/andrea-ragalzi/document-intelligent-hub"
    );
    expect(githubLink).toHaveAttribute("target", "_blank");
    expect(screen.getByRole("link", { name: "About" })).toHaveAttribute("href", "/about");
  });

  it("sends authenticated visitors from the landing page to the dashboard", async () => {
    mocks.auth.user = { uid: "recruiter" };
    render(<LandingPage />);

    await waitFor(() => expect(mocks.push).toHaveBeenCalledWith("/dashboard"));
  });

  it("returns public About visitors to the landing page", () => {
    render(<AboutPage />);

    expect(screen.getByText(/independent full-stack RAG application/i)).toBeInTheDocument();
    expect(screen.getByText("Technical overview")).toBeInTheDocument();
    expect(screen.getByText("Python · FastAPI · Pydantic")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Andrea Ragalzi" })).toHaveAttribute(
      "href",
      "https://andrea-ragalzi.github.io/"
    );
    fireEvent.click(screen.getByText("Back to home", { selector: "button" }));
    expect(mocks.push).toHaveBeenCalledWith("/");
  });

  it("returns signed-in About visitors to the dashboard", () => {
    mocks.auth.user = { uid: "recruiter" };
    render(<AboutPage />);

    fireEvent.click(screen.getByText("Back to dashboard", { selector: "button" }));
    expect(mocks.push).toHaveBeenCalledWith("/dashboard");
  });
});
