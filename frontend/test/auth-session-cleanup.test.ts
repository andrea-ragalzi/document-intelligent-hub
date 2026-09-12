import { beforeEach, describe, expect, it, vi } from "vitest";
import { clearUserScopedClientState } from "@/lib/authSessionCleanup";
import { CONVERSATIONS_KEY } from "@/lib/constants";
import { useUIStore } from "@/stores/uiStore";

describe("authentication session cleanup", () => {
  beforeEach(() => {
    localStorage.clear();
    useUIStore.getState().resetConversation();
  });

  it("removes user-scoped fallback data and resets conversation tracking", () => {
    localStorage.setItem(CONVERSATIONS_KEY, "previous-user-data");
    useUIStore.getState().setCurrentConversation("previous-conversation");
    useUIStore.getState().updateSavedMessageCount(4);

    clearUserScopedClientState();

    expect(localStorage.getItem(CONVERSATIONS_KEY)).toBeNull();
    expect(useUIStore.getState().currentConversationId).toBeNull();
    expect(useUIStore.getState().lastSavedMessageCount).toBe(0);
  });

  it("keeps logout successful when browser storage is unavailable", () => {
    useUIStore.getState().setCurrentConversation("previous-conversation");
    vi.spyOn(localStorage, "removeItem").mockImplementationOnce(() => {
      throw new Error("storage unavailable");
    });

    expect(() => clearUserScopedClientState()).not.toThrow();
    expect(useUIStore.getState().currentConversationId).toBeNull();
  });
});
