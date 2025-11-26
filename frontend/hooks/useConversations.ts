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

export const useConversations = ({
  currentChatHistory,
  userId,
}: UseConversationsParams) => {
  const [savedConversations, setSavedConversations] = useState<
    SavedConversation[]
  >([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load conversations on mount
  useEffect(() => {
    if (!userId) return;

    const loadConversations = async () => {
      setIsLoading(true);
      setError(null);

      try {
        // Try loading from Firestore
        const firestoreConversations = await loadConversationsFromFirestore(
          userId
        );

        // If no conversations in Firestore, check localStorage for migration
        if (
          firestoreConversations.length === 0 &&
          globalThis.window !== undefined
        ) {
          const stored = localStorage.getItem(CONVERSATIONS_KEY);
          if (stored) {
            try {
              const localConversations: SavedConversation[] =
                JSON.parse(stored);
              if (localConversations.length > 0) {
                // Migrate to Firestore
                console.log(
                  "Migrating conversations from localStorage to Firestore..."
                );
                await migrateLocalStorageToFirestore(
                  userId,
                  localConversations
                );
                // Reload from Firestore
                const migratedConversations =
                  await loadConversationsFromFirestore(userId);
                setSavedConversations(migratedConversations);
                // Clean localStorage after migration
                localStorage.removeItem(CONVERSATIONS_KEY);
                return;
              }
            } catch (e) {
              console.error("Error migrating from localStorage:", e);
            }
          }
        }

        setSavedConversations(firestoreConversations);
      } catch (err) {
        console.error("Error loading conversations:", err);
        setError("Unable to load conversations");

        // Fallback to localStorage if Firestore fails
        if (globalThis.window !== undefined) {
          const stored = localStorage.getItem(CONVERSATIONS_KEY);
          if (stored) {
            try {
              const parsed = JSON.parse(stored);
              setSavedConversations(parsed);
            } catch (e) {
              console.error("Error parsing localStorage conversations:", e);
            }
          }
        }
      } finally {
        setIsLoading(false);
      }
    };

    loadConversations();
  }, [userId]);

  // Save a conversation
  const saveConversation = useCallback(
    async (name: string): Promise<boolean> => {
      console.log("🗂️ useConversations.saveConversation called");
      console.log("  name:", name);
      console.log("  userId:", userId);
      console.log("  currentChatHistory.length:", currentChatHistory.length);

      if (!userId) {
        console.log("❌ No userId");
        setError("User ID not available");
        return false;
      }
      if (currentChatHistory.length === 0) {
        console.log("❌ No chat history");
        setError("No conversation to save");
        return false;
      }

      console.log("📝 Starting save process...");
      setIsLoading(true);
      setError(null);

      try {
        console.log("🔥 Calling Firestore...");
        // Salva su Firestore (rimosso timeout per vedere l'errore reale)
        const newConversation = await saveConversationToFirestore(
          userId,
          name,
          currentChatHistory
        );

        console.log("✅ Got response from Firestore:", newConversation);

        // Aggiorna lo stato locale
        setSavedConversations((prev) => [newConversation, ...prev]);

        // Backup su localStorage
        if (globalThis.window !== undefined) {
          const updated = [newConversation, ...savedConversations];
          localStorage.setItem(CONVERSATIONS_KEY, JSON.stringify(updated));
        }

        console.log("🎉 Save completed successfully");
        return true;
      } catch (err) {
        console.error("❌ Error saving conversation:", err);
        console.error("❌ Error details:", JSON.stringify(err, null, 2));
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
          } catch (error_) {
            // Intentional: localStorage errors should not block the save flow
            console.error("Error saving to localStorage:", error_);
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
        const updated = savedConversations.filter((conv) => conv.id !== id);
        setSavedConversations(updated);

        // Update localStorage
        if (globalThis.window !== undefined) {
          localStorage.setItem(CONVERSATIONS_KEY, JSON.stringify(updated));
        }

        return true;
      } catch (err) {
        console.error("Error deleting conversation:", err);
        setError("Unable to delete conversation");

        // Fallback to localStorage
        if (globalThis.window !== undefined) {
          try {
            const updated = savedConversations.filter((conv) => conv.id !== id);
            localStorage.setItem(CONVERSATIONS_KEY, JSON.stringify(updated));
            setSavedConversations(updated);
            return true;
          } catch (error_) {
            // Intentional: localStorage errors should not block the delete flow
            console.error("Error deleting from localStorage:", error_);
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

      console.log("✏️ Renaming conversation:", id, "to:", newName);
      setIsLoading(true);
      setError(null);

      try {
        // Update in Firestore
        const { updateConversationNameInFirestore } = await import(
          "@/lib/conversationsService"
        );
        await updateConversationNameInFirestore(id, newName);

        // Update local state
        const updated = savedConversations.map((conv) =>
          conv.id === id ? { ...conv, name: newName } : conv
        );
        setSavedConversations(updated);

        // Update localStorage
        if (globalThis.window !== undefined) {
          localStorage.setItem(CONVERSATIONS_KEY, JSON.stringify(updated));
        }

        return true;
      } catch (err) {
        console.error("Error renaming conversation:", err);
        setError("Unable to rename conversation");

        // Fallback to localStorage
        if (globalThis.window !== undefined) {
          try {
            const updated = savedConversations.map((conv) =>
              conv.id === id ? { ...conv, name: newName } : conv
            );
            localStorage.setItem(CONVERSATIONS_KEY, JSON.stringify(updated));
            setSavedConversations(updated);
            return true;
          } catch (error_) {
            // Intentional: localStorage errors should not block the rename flow
            console.error("Error updating localStorage:", error_);
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

      console.log("📝 Updating conversation history:", id);
      setIsLoading(true);
      setError(null);

      try {
        // Update in Firestore
        const { updateConversationHistoryInFirestore } = await import(
          "@/lib/conversationsService"
        );
        await updateConversationHistoryInFirestore(id, history);

        // Update local state
        const updated = savedConversations.map((conv) =>
          conv.id === id ? { ...conv, history } : conv
        );
        setSavedConversations(updated);

        // Update localStorage
        if (globalThis.window !== undefined) {
          localStorage.setItem(CONVERSATIONS_KEY, JSON.stringify(updated));
        }

        return true;
      } catch (err) {
        console.error("Error updating conversation history:", err);
        setError("Unable to update conversation");

        // Fallback to localStorage
        if (globalThis.window !== undefined) {
          try {
            const updated = savedConversations.map((conv) =>
              conv.id === id ? { ...conv, history } : conv
            );
            localStorage.setItem(CONVERSATIONS_KEY, JSON.stringify(updated));
            setSavedConversations(updated);
            return true;
          } catch (error_) {
            // Intentional: localStorage errors should not block the update flow
            console.error("Error updating localStorage:", error_);
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
