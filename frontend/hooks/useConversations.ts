"use client";

import { useState, useEffect, useCallback } from "react";
import type { ChatMessage, SavedConversation } from "@/lib/types";
import { CONVERSATIONS_KEY } from "@/lib/constants";
import {
  saveConversationToFirestore,
  loadConversationsFromFirestore,
  deleteConversationFromFirestore,
  migrateLocalStorageToFirestore,
} from "@/lib/conversationsService";

interface UseConversationsParams {
  currentChatHistory: ChatMessage[];
  userId: string | null;
}

export const useConversations = ({ currentChatHistory, userId }: UseConversationsParams) => {
  const [savedConversations, setSavedConversations] = useState<SavedConversation[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Helper: Try to load and parse from localStorage
  const tryLoadFromLocalStorage = useCallback((): SavedConversation[] => {
    if (globalThis.window === undefined) return [];

    const stored = localStorage.getItem(CONVERSATIONS_KEY);
    if (!stored) return [];

    try {
      return JSON.parse(stored);
    } catch {
      console.error("Unable to parse saved conversations.");
      return [];
    }
  }, []);

  // Helper: Handle localStorage migration to Firestore
  const handleLocalStorageMigration = useCallback(
    async (userId: string): Promise<SavedConversation[]> => {
      const localConversations = tryLoadFromLocalStorage();

      if (localConversations.length === 0) return [];

      await migrateLocalStorageToFirestore(userId, localConversations);

      const migratedConversations = await loadConversationsFromFirestore(userId);
      localStorage.removeItem(CONVERSATIONS_KEY);

      return migratedConversations;
    },
    [tryLoadFromLocalStorage]
  );

  // Load conversations on mount
  useEffect(() => {
    if (!userId) return;

    const loadConversations = async () => {
      setIsLoading(true);
      setError(null);

      try {
        // Try loading from Firestore
        const firestoreConversations = await loadConversationsFromFirestore(userId);

        // If no conversations in Firestore, check localStorage for migration
        if (firestoreConversations.length === 0 && globalThis.window !== undefined) {
          try {
            const migratedConversations = await handleLocalStorageMigration(userId);
            if (migratedConversations.length > 0) {
              setSavedConversations(migratedConversations);
              return;
            }
          } catch {
            console.error("Unable to migrate saved conversations.");
          }
        }

        setSavedConversations(firestoreConversations);
      } catch {
        console.error("Unable to load conversations.");
        setError("Unable to load conversations");

        // Fallback to localStorage if Firestore fails
        const localConversations = tryLoadFromLocalStorage();
        setSavedConversations(localConversations);
      } finally {
        setIsLoading(false);
      }
    };

    loadConversations();
  }, [userId, handleLocalStorageMigration, tryLoadFromLocalStorage]);

  // Save a conversation
  const saveConversation = useCallback(
    async (name: string): Promise<boolean> => {
      if (!userId) {
        setError("User ID not available");
        return false;
      }
      if (currentChatHistory.length === 0) {
        setError("No conversation to save");
        return false;
      }

      setIsLoading(true);
      setError(null);

      try {
        // Salva su Firestore (rimosso timeout per vedere l'errore reale)
        const newConversation = await saveConversationToFirestore(userId, name, currentChatHistory);

        // Aggiorna lo stato locale
        setSavedConversations(prev => [newConversation, ...prev]);

        // Backup su localStorage
        if (globalThis.window !== undefined) {
          const updated = [newConversation, ...savedConversations];
          localStorage.setItem(CONVERSATIONS_KEY, JSON.stringify(updated));
        }

        return true;
      } catch {
        console.error("Unable to save conversation.");
        setError("Unable to save conversation");

        // Fallback to localStorage
        if (globalThis.window !== undefined) {
          try {
            const newConversation: SavedConversation = {
              id: Date.now().toString(),
              userId,
              name,
              timestamp: new Date().toLocaleString("it-IT"),
              history: currentChatHistory,
            };
            const updated = [newConversation, ...savedConversations];
            localStorage.setItem(CONVERSATIONS_KEY, JSON.stringify(updated));
            setSavedConversations(updated);
            return true;
          } catch {
            // Intentional: localStorage errors should not block the save flow
            console.error("Unable to save conversation locally.");
          }
        }

        return false;
      } finally {
        setIsLoading(false);
      }
    },
    [userId, currentChatHistory, savedConversations]
  );

  // Delete a conversation
  const deleteConversation = useCallback(
    async (id: string): Promise<boolean> => {
      setIsLoading(true);
      setError(null);

      try {
        // Delete from Firestore
        await deleteConversationFromFirestore(id);

        // Update local state
        const updated = savedConversations.filter(conv => conv.id !== id);
        setSavedConversations(updated);

        // Update localStorage
        if (globalThis.window !== undefined) {
          localStorage.setItem(CONVERSATIONS_KEY, JSON.stringify(updated));
        }

        return true;
      } catch {
        console.error("Unable to delete conversation.");
        setError("Unable to delete conversation");

        // Fallback to localStorage
        if (globalThis.window !== undefined) {
          try {
            const updated = savedConversations.filter(conv => conv.id !== id);
            localStorage.setItem(CONVERSATIONS_KEY, JSON.stringify(updated));
            setSavedConversations(updated);
            return true;
          } catch {
            // Intentional: localStorage errors should not block the delete flow
            console.error("Unable to delete the local conversation copy.");
          }
        }

        return false;
      } finally {
        setIsLoading(false);
      }
    },
    [savedConversations]
  );

  // Rename a conversation
  const updateConversationName = useCallback(
    async (id: string, newName: string): Promise<boolean> => {
      if (!userId) {
        console.error("Cannot rename: userId is null");
        return false;
      }

      setIsLoading(true);
      setError(null);

      try {
        // Update in Firestore
        const { updateConversationNameInFirestore } = await import("@/lib/conversationsService");
        await updateConversationNameInFirestore(id, newName);

        // Update local state
        const updated = savedConversations.map(conv =>
          conv.id === id ? { ...conv, name: newName } : conv
        );
        setSavedConversations(updated);

        // Update localStorage
        if (globalThis.window !== undefined) {
          localStorage.setItem(CONVERSATIONS_KEY, JSON.stringify(updated));
        }

        return true;
      } catch {
        console.error("Unable to rename conversation.");
        setError("Unable to rename conversation");

        // Fallback to localStorage
        if (globalThis.window !== undefined) {
          try {
            const updated = savedConversations.map(conv =>
              conv.id === id ? { ...conv, name: newName } : conv
            );
            localStorage.setItem(CONVERSATIONS_KEY, JSON.stringify(updated));
            setSavedConversations(updated);
            return true;
          } catch {
            // Intentional: localStorage errors should not block the rename flow
            console.error("Unable to update the local conversation copy.");
          }
        }

        return false;
      } finally {
        setIsLoading(false);
      }
    },
    [savedConversations, userId]
  );

  // Update conversation history
  const updateConversationHistory = useCallback(
    async (id: string, history: ChatMessage[]): Promise<boolean> => {
      if (!userId) {
        console.error("Cannot update history: userId is null");
        return false;
      }

      setIsLoading(true);
      setError(null);

      try {
        // Update in Firestore
        const { updateConversationHistoryInFirestore } = await import("@/lib/conversationsService");
        await updateConversationHistoryInFirestore(id, history);

        // Update local state
        const updated = savedConversations.map(conv =>
          conv.id === id ? { ...conv, history } : conv
        );
        setSavedConversations(updated);

        // Update localStorage
        if (globalThis.window !== undefined) {
          localStorage.setItem(CONVERSATIONS_KEY, JSON.stringify(updated));
        }

        return true;
      } catch {
        console.error("Unable to update conversation history.");
        setError("Unable to update conversation");

        // Fallback to localStorage
        if (globalThis.window !== undefined) {
          try {
            const updated = savedConversations.map(conv =>
              conv.id === id ? { ...conv, history } : conv
            );
            localStorage.setItem(CONVERSATIONS_KEY, JSON.stringify(updated));
            setSavedConversations(updated);
            return true;
          } catch {
            // Intentional: localStorage errors should not block the update flow
            console.error("Unable to update the local conversation copy.");
          }
        }

        return false;
      } finally {
        setIsLoading(false);
      }
    },
    [savedConversations, userId]
  );

  return {
    savedConversations,
    saveConversation,
    deleteConversation,
    updateConversationName,
    updateConversationHistory,
    isLoading,
    error,
  };
};

// Utility functions for UPDATE (to use directly where needed)
export {
  updateConversationNameInFirestore,
  updateConversationHistoryInFirestore,
} from "@/lib/conversationsService";
