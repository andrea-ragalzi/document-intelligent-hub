import { create } from "zustand";
import { devtools } from "zustand/middleware";
import type { AlertState } from "@/lib/types";

/**
 * UI Store - Gestisce tutto lo stato dell'interfaccia utente
 * Separato dal server state (conversazioni) che è gestito da TanStack Query
 */
interface UIStore {
  // Alert states
  statusAlert: AlertState | null;
  uploadAlert: AlertState | null;

  // Modal states
  renameModalOpen: boolean;
  confirmDeleteOpen: boolean;
  conversationToRename: { id: string; currentName: string } | null;
  conversationToDelete: { id: string; name: string } | null;

  // Conversation tracking
  currentConversationId: string | null;
  lastSavedMessageCount: number;
  isSaving: boolean;

  // Theme (potremmo spostare anche questo qui in futuro)
  // theme: 'light' | 'dark';

  // Actions - Alert
  setStatusAlert: (alert: AlertState | null) => void;
  setUploadAlert: (alert: AlertState | null) => void;

  // Actions - Rename Modal
  openRenameModal: (id: string, currentName: string) => void;
  closeRenameModal: () => void;

  // Actions - Delete Modal
  openDeleteModal: (id: string, name: string) => void;
  closeDeleteModal: () => void;

  // Actions - Conversation tracking
  setCurrentConversation: (id: string | null) => void;
  updateSavedMessageCount: (count: number) => void;
  startSaving: () => void;
  finishSaving: () => void;
  resetConversation: () => void;
}

export const useUIStore = create<UIStore>()(
  devtools(
    (set) => ({
      // Initial state
      statusAlert: null,
      uploadAlert: null,
      renameModalOpen: false,
      confirmDeleteOpen: false,
      conversationToRename: null,
      conversationToDelete: null,
      currentConversationId: null,
      lastSavedMessageCount: 0,
      isSaving: false,

      // Alert actions
      setStatusAlert: (alert) => set({ statusAlert: alert }),
      setUploadAlert: (alert) => set({ uploadAlert: alert }),

      // Rename modal actions
      openRenameModal: (id, currentName) =>
        set({
          renameModalOpen: true,
          conversationToRename: { id, currentName },
        }),
      closeRenameModal: () =>
        set({
          renameModalOpen: false,
          conversationToRename: null,
        }),

      // Delete modal actions
      openDeleteModal: (id, name) =>
        set({
          confirmDeleteOpen: true,
          conversationToDelete: { id, name },
        }),
      closeDeleteModal: () =>
        set({
          confirmDeleteOpen: false,
          conversationToDelete: null,
        }),

      // Conversation tracking actions
      setCurrentConversation: (id) => set({ currentConversationId: id }),
      updateSavedMessageCount: (count) => set({ lastSavedMessageCount: count }),
      startSaving: () => set({ isSaving: true }),
      finishSaving: () => set({ isSaving: false }),
      resetConversation: () =>
        set({
          currentConversationId: null,
          lastSavedMessageCount: 0,
        }),
    }),
    { name: "UI Store" }
  )
);
