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

  // Carica le conversazioni all'avvio
  useEffect(() => {
    if (!userId) return;

    const loadConversations = async () => {
      setIsLoading(true);
      setError(null);

      try {
        // Prova a caricare da Firestore
        const firestoreConversations = await loadConversationsFromFirestore(
          userId
        );

        // Se non ci sono conversazioni su Firestore, controlla localStorage per migrare
        if (
          firestoreConversations.length === 0 &&
          typeof window !== "undefined"
        ) {
          const stored = localStorage.getItem(CONVERSATIONS_KEY);
          if (stored) {
            try {
              const localConversations: SavedConversation[] =
                JSON.parse(stored);
              if (localConversations.length > 0) {
                // Migra a Firestore
                console.log(
                  "Migrating conversations from localStorage to Firestore..."
                );
                await migrateLocalStorageToFirestore(
                  userId,
                  localConversations
                );
                // Ricarica da Firestore
                const migratedConversations =
                  await loadConversationsFromFirestore(userId);
                setSavedConversations(migratedConversations);
                // Pulisci localStorage dopo la migrazione
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
        setError("Impossibile caricare le conversazioni");

        // Fallback a localStorage se Firestore fallisce
        if (typeof window !== "undefined") {
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

  // Salva una conversazione
  const saveConversation = useCallback(
    async (name: string): Promise<boolean> => {
      console.log("🗂️ useConversations.saveConversation called");
      console.log("  name:", name);
      console.log("  userId:", userId);
      console.log("  currentChatHistory.length:", currentChatHistory.length);

      if (!userId) {
        console.log("❌ No userId");
        setError("User ID non disponibile");
        return false;
      }
      if (currentChatHistory.length === 0) {
        console.log("❌ No chat history");
        setError("Nessuna conversazione da salvare");
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
        if (typeof window !== "undefined") {
          const updated = [newConversation, ...savedConversations];
          localStorage.setItem(CONVERSATIONS_KEY, JSON.stringify(updated));
        }

        console.log("🎉 Save completed successfully");
        return true;
      } catch (err) {
        console.error("❌ Error saving conversation:", err);
        console.error("❌ Error details:", JSON.stringify(err, null, 2));
        setError("Impossibile salvare la conversazione");

        // Fallback a localStorage
        if (typeof window !== "undefined") {
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
          } catch (localErr) {
            console.error("Error saving to localStorage:", localErr);
          }
        }

        return false;
      } finally {
        setIsLoading(false);
      }
    },
    [userId, currentChatHistory, savedConversations]
  );

  // Elimina una conversazione
  const deleteConversation = useCallback(
    async (id: string): Promise<boolean> => {
      setIsLoading(true);
      setError(null);

      try {
        // Elimina da Firestore
        await deleteConversationFromFirestore(id);

        // Aggiorna lo stato locale
        const updated = savedConversations.filter((conv) => conv.id !== id);
        setSavedConversations(updated);

        // Aggiorna localStorage
        if (typeof window !== "undefined") {
          localStorage.setItem(CONVERSATIONS_KEY, JSON.stringify(updated));
        }

        return true;
      } catch (err) {
        console.error("Error deleting conversation:", err);
        setError("Impossibile eliminare la conversazione");

        // Fallback a localStorage
        if (typeof window !== "undefined") {
          try {
            const updated = savedConversations.filter((conv) => conv.id !== id);
            localStorage.setItem(CONVERSATIONS_KEY, JSON.stringify(updated));
            setSavedConversations(updated);
            return true;
          } catch (localErr) {
            console.error("Error deleting from localStorage:", localErr);
          }
        }

        return false;
      } finally {
        setIsLoading(false);
      }
    },
    [savedConversations]
  );

  // Rinomina una conversazione
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
        // Aggiorna in Firestore
        const { updateConversationNameInFirestore } = await import(
          "@/lib/conversationsService"
        );
        await updateConversationNameInFirestore(id, newName);

        // Aggiorna lo stato locale
        const updated = savedConversations.map((conv) =>
          conv.id === id ? { ...conv, name: newName } : conv
        );
        setSavedConversations(updated);

        // Aggiorna localStorage
        if (typeof window !== "undefined") {
          localStorage.setItem(CONVERSATIONS_KEY, JSON.stringify(updated));
        }

        return true;
      } catch (err) {
        console.error("Error renaming conversation:", err);
        setError("Impossibile rinominare la conversazione");

        // Fallback a localStorage
        if (typeof window !== "undefined") {
          try {
            const updated = savedConversations.map((conv) =>
              conv.id === id ? { ...conv, name: newName } : conv
            );
            localStorage.setItem(CONVERSATIONS_KEY, JSON.stringify(updated));
            setSavedConversations(updated);
            return true;
          } catch (localErr) {
            console.error("Error updating localStorage:", localErr);
          }
        }

        return false;
      } finally {
        setIsLoading(false);
      }
    },
    [savedConversations, userId]
  );

  // Aggiorna la history di una conversazione
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
        // Aggiorna in Firestore
        const { updateConversationHistoryInFirestore } = await import(
          "@/lib/conversationsService"
        );
        await updateConversationHistoryInFirestore(id, history);

        // Aggiorna lo stato locale
        const updated = savedConversations.map((conv) =>
          conv.id === id ? { ...conv, history } : conv
        );
        setSavedConversations(updated);

        // Aggiorna localStorage
        if (typeof window !== "undefined") {
          localStorage.setItem(CONVERSATIONS_KEY, JSON.stringify(updated));
        }

        return true;
      } catch (err) {
        console.error("Error updating conversation history:", err);
        setError("Impossibile aggiornare la conversazione");

        // Fallback a localStorage
        if (typeof window !== "undefined") {
          try {
            const updated = savedConversations.map((conv) =>
              conv.id === id ? { ...conv, history } : conv
            );
            localStorage.setItem(CONVERSATIONS_KEY, JSON.stringify(updated));
            setSavedConversations(updated);
            return true;
          } catch (localErr) {
            console.error("Error updating localStorage:", localErr);
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

// Funzioni di utility per UPDATE (da usare direttamente dove serve)
export {
  updateConversationNameInFirestore,
  updateConversationHistoryInFirestore,
} from "@/lib/conversationsService";
