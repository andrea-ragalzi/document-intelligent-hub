import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { FeedbackModal } from "@/components/FeedbackModal";

const getIdToken = vi.fn().mockResolvedValue("firebase-test-token");
vi.mock("@/contexts/AuthContext", () => ({ useAuth: () => ({ getIdToken }) }));

describe("FeedbackModal", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    process.env.NEXT_PUBLIC_API_BASE_URL = "https://api.example/rag";
    globalThis.fetch = vi.fn().mockResolvedValue({ ok: true } as Response);
  });

  it("posts feedback to the canonical trailing-slash endpoint", async () => {
    render(<FeedbackModal isOpen onClose={vi.fn()} />);
    fireEvent.change(screen.getByLabelText(/your feedback/i), {
      target: { value: "Useful application." },
    });
    fireEvent.click(screen.getByRole("button", { name: /submit feedback/i }));

    await waitFor(() => expect(globalThis.fetch).toHaveBeenCalled());
    expect(vi.mocked(globalThis.fetch).mock.calls[0][0]).toBe("https://api.example/rag/feedback/");
  });
});
