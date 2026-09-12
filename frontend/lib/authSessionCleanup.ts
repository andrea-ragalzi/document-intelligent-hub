import { CONVERSATIONS_KEY } from "@/lib/constants";
import { useUIStore } from "@/stores/uiStore";

/** Clear user-scoped client state after Firebase has signed the user out. */
export function clearUserScopedClientState(): void {
  if (typeof window !== "undefined") {
    try {
      window.localStorage.removeItem(CONVERSATIONS_KEY);
    } catch (error) {
      // Firebase is already signed out; unavailable browser storage must not
      // turn a successful sign-out into an authentication failure.
      console.warn("Could not clear local conversation fallback after sign-out", error);
    }
  }
  useUIStore.getState().resetConversation();
}
