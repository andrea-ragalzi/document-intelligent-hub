/**
 * TanStack Query hooks per gestire le conversazioni con Firestore
 *
 * Questo file sostituisce useConversations.ts con una gestione
 * più robusta dello stato del server tramite TanStack Query.
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import type { SavedConversation, ChatMessage } from "@/lib/types";
import {
  loadConversationsFromFirestore,
  saveConversationToFirestore,
  deleteConversationFromFirestore,
  updateConversationNameInFirestore,
  updateConversationHistoryInFirestore,
} from "@/lib/conversationsService";

// Query keys per TanStack Query
export const conversationKeys = {
  all: ["conversations"] as const,
  byUser: (userId: string) => ["conversations", userId] as const,
  detail: (id: string) => ["conversations", "detail", id] as const,
};

/**
 * Hook per caricare tutte le conversazioni di un utente
 *
 * Features:
 * - Auto-refetch quando la query diventa stale
 * - Cache automatica
 * - Loading e error states gestiti
 */
export function useConversationsQuery(userId: string | null) {
  return useQuery({
    queryKey: conversationKeys.byUser(userId || ""),
    queryFn: () => {
      if (!userId) throw new Error("User ID required");
      return loadConversationsFromFirestore(userId);
    },
    enabled: !!userId, // Esegui solo se userId è presente
    staleTime: 30 * 1000, // 30 secondi
  });
}

/**
 * Mutation per creare una nuova conversazione
 *
 * Features:
 * - Optimistic update (aggiunge subito alla cache)
 * - Rollback automatico in caso di errore
 * - Invalida e refetch dopo successo
 */
export function useCreateConversation(userId: string | null) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      name,
      history,
    }: {
      name: string;
      history: ChatMessage[];
    }) => {
      if (!userId) throw new Error("User ID required");
      return saveConversationToFirestore(userId, name, history);
    },

    // Optimistic update: aggiungi subito alla cache
    onMutate: async (newConversation) => {
      // Cancella refetch in corso
      await queryClient.cancelQueries({
        queryKey: conversationKeys.byUser(userId || ""),
      });

      // Snapshot del valore precedente
      const previousConversations = queryClient.getQueryData<
        SavedConversation[]
      >(conversationKeys.byUser(userId || ""));

      // Optimistic update: aggiungi conversazione temporanea
      queryClient.setQueryData<SavedConversation[]>(
        conversationKeys.byUser(userId || ""),
        (old) => {
          const tempConv: SavedConversation = {
            id: "temp-" + Date.now(),
            userId: userId || "",
            name: newConversation.name,
            timestamp: new Date().toLocaleString("it-IT"),
            history: newConversation.history,
          };
          return [tempConv, ...(old || [])];
        }
      );

      return { previousConversations };
    },

    // Rollback in caso di errore
    onError: (err, newConversation, context) => {
      console.error("❌ Error creating conversation:", err);
      if (context?.previousConversations) {
        queryClient.setQueryData(
          conversationKeys.byUser(userId || ""),
          context.previousConversations
        );
      }
    },

    // Refetch dopo successo
    onSuccess: (data) => {
      console.log("✅ Conversation created:", data.id);
      queryClient.invalidateQueries({
        queryKey: conversationKeys.byUser(userId || ""),
      });
    },
  });
}

/**
 * Mutation per aggiornare il nome di una conversazione
 */
export function useUpdateConversationName(userId: string | null) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, newName }: { id: string; newName: string }) =>
      updateConversationNameInFirestore(id, newName),

    // Optimistic update
    onMutate: async ({ id, newName }) => {
      await queryClient.cancelQueries({
        queryKey: conversationKeys.byUser(userId || ""),
      });

      const previousConversations = queryClient.getQueryData<
        SavedConversation[]
      >(conversationKeys.byUser(userId || ""));

      queryClient.setQueryData<SavedConversation[]>(
        conversationKeys.byUser(userId || ""),
        (old) =>
          old?.map((conv) =>
            conv.id === id ? { ...conv, name: newName } : conv
          ) || []
      );

      return { previousConversations };
    },

    onError: (err, variables, context) => {
      console.error("❌ Error updating conversation name:", err);
      if (context?.previousConversations) {
        queryClient.setQueryData(
          conversationKeys.byUser(userId || ""),
          context.previousConversations
        );
      }
    },

    onSuccess: () => {
      console.log("✅ Conversation name updated");
      queryClient.invalidateQueries({
        queryKey: conversationKeys.byUser(userId || ""),
      });
    },
  });
}

/**
 * Mutation per aggiornare la history di una conversazione (auto-save)
 */
export function useUpdateConversationHistory(userId: string | null) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, history }: { id: string; history: ChatMessage[] }) =>
      updateConversationHistoryInFirestore(id, history),

    // Optimistic update
    onMutate: async ({ id, history }) => {
      await queryClient.cancelQueries({
        queryKey: conversationKeys.byUser(userId || ""),
      });

      const previousConversations = queryClient.getQueryData<
        SavedConversation[]
      >(conversationKeys.byUser(userId || ""));

      queryClient.setQueryData<SavedConversation[]>(
        conversationKeys.byUser(userId || ""),
        (old) =>
          old?.map((conv) => (conv.id === id ? { ...conv, history } : conv)) ||
          []
      );

      return { previousConversations };
    },

    onError: (err, variables, context) => {
      console.error("❌ Error updating conversation history:", err);
      if (context?.previousConversations) {
        queryClient.setQueryData(
          conversationKeys.byUser(userId || ""),
          context.previousConversations
        );
      }
    },

    // Non fare refetch per auto-save (troppo costoso)
    onSuccess: (_, variables) => {
      console.log("✅ Conversation history updated:", variables.id);
      // Invalida ma non refetch automaticamente
      queryClient.invalidateQueries({
        queryKey: conversationKeys.byUser(userId || ""),
        refetchType: "none",
      });
    },
  });
}

/**
 * Mutation per eliminare una conversazione
 */
export function useDeleteConversation(userId: string | null) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => deleteConversationFromFirestore(id),

    // Optimistic update
    onMutate: async (id) => {
      await queryClient.cancelQueries({
        queryKey: conversationKeys.byUser(userId || ""),
      });

      const previousConversations = queryClient.getQueryData<
        SavedConversation[]
      >(conversationKeys.byUser(userId || ""));

      queryClient.setQueryData<SavedConversation[]>(
        conversationKeys.byUser(userId || ""),
        (old) => old?.filter((conv) => conv.id !== id) || []
      );

      return { previousConversations };
    },

    onError: (err, variables, context) => {
      console.error("❌ Error deleting conversation:", err);
      if (context?.previousConversations) {
        queryClient.setQueryData(
          conversationKeys.byUser(userId || ""),
          context.previousConversations
        );
      }
    },

    onSuccess: (_, deletedId) => {
      console.log("✅ Conversation deleted:", deletedId);
      queryClient.invalidateQueries({
        queryKey: conversationKeys.byUser(userId || ""),
      });
    },
  });
}
