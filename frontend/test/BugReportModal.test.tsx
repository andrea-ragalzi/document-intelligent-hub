import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { BugReportModal } from "@/components/BugReportModal";

const getIdToken = vi.fn().mockResolvedValue("firebase-test-token");
vi.mock("@/contexts/AuthContext", () => ({ useAuth: () => ({ getIdToken }) }));

describe("BugReportModal", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    globalThis.fetch = vi.fn();
  });

  it("accepts only the screenshot formats and client size boundary", () => {
    render(<BugReportModal isOpen onClose={vi.fn()} />);
    const input = screen.getByLabelText(/attach screenshot/i);
    expect(input).toHaveAttribute("accept", "image/png,image/jpeg,image/webp");
    fireEvent.change(input, {
      target: { files: [new File(["x"], "clip.mp4", { type: "video/mp4" })] },
    });
    expect(screen.getByText(/only PNG, JPEG, and WebP/i)).toBeInTheDocument();
  });

  it("does not send a client user ID", async () => {
    vi.mocked(globalThis.fetch).mockResolvedValue({ ok: true } as Response);
    render(<BugReportModal isOpen onClose={vi.fn()} />);
    fireEvent.change(screen.getByLabelText(/describe the bug/i), {
      target: { value: "The upload button did not respond." },
    });
    fireEvent.click(screen.getByRole("button", { name: /submit report/i }));
    await waitFor(() => expect(globalThis.fetch).toHaveBeenCalled());
    const body = vi.mocked(globalThis.fetch).mock.calls[0][1]?.body as FormData;
    expect(body.get("user_id")).toBeNull();
  });

  it("posts a screenshot report to the canonical multipart endpoint", async () => {
    process.env.NEXT_PUBLIC_API_BASE_URL = "https://api.example/rag";
    vi.mocked(globalThis.fetch).mockResolvedValue({ ok: true } as Response);
    render(<BugReportModal isOpen onClose={vi.fn()} />);
    fireEvent.change(screen.getByLabelText(/describe the bug/i), {
      target: { value: "The upload button did not respond." },
    });
    fireEvent.change(screen.getByLabelText(/attach screenshot/i), {
      target: { files: [new File(["png"], "screen.png", { type: "image/png" })] },
    });
    fireEvent.click(screen.getByRole("button", { name: /submit report/i }));

    await waitFor(() => expect(globalThis.fetch).toHaveBeenCalled());
    const [url, options] = vi.mocked(globalThis.fetch).mock.calls[0];
    expect(url).toBe("https://api.example/rag/report-bug/");
    expect(options?.headers).toMatchObject({ Authorization: "Bearer firebase-test-token" });
    expect((options?.body as FormData).get("attachment")).toBeInstanceOf(File);
  });
});
