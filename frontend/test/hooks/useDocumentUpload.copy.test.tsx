import { renderHook } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { useDocumentUpload } from "@/hooks/useDocumentUpload";

vi.mock("@/contexts/AuthContext", () => ({
  useAuth: () => ({ getIdToken: vi.fn() }),
}));

describe("useDocumentUpload", () => {
  it("does not ask an authenticated user to enter a UID", () => {
    const { result } = renderHook(() => useDocumentUpload());
    expect(result.current.uploadAlert.message).toBe("Select a PDF to upload.");
  });
});
