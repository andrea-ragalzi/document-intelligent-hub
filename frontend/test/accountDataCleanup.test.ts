import { describe, expect, it, vi } from "vitest";
import { deleteAccountData } from "@/lib/accountDataCleanup";

describe("account data cleanup", () => {
  it("uses the authenticated cleanup endpoint", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(null, { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    await deleteAccountData("fresh-token");

    expect(fetchMock).toHaveBeenCalledWith("http://127.0.0.1:8000/rag/account/data", {
      method: "DELETE",
      headers: { Authorization: "Bearer fresh-token" },
    });
  });

  it("fails before Firebase Auth deletion can be attempted when cleanup is rejected", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(null, { status: 500 })));

    await expect(deleteAccountData("fresh-token")).rejects.toThrow("Unable to delete account data");
  });
});
