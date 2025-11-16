/**
 * TanStack Query hooks to manage conversations with Firestore
 *
 * This file replaces useConversations.ts with more robust
 * server state management through TanStack Query.
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

// Query keys for TanStack Query
export const conversationKeys = {
  all: ["conversations"] as const,
  byUser: (userId: string) => ["conversations", userId] as const,
  detail: (id: string) => ["conversations", "detail", id] as const,
};

/**
 * Hook to load all conversations for a user
 *
 * Features:
 * - Auto-refetch when query becomes stale
 * - Automatic caching
 * - Managed loading and error states
 */
export function useConversationsQuery(userId: string | null) {
  return useQuery({
    queryKey: conversationKeys.byUser(userId || ""),
    queryFn: () => {
      if (!userId) throw new Error("User ID required");
      return loadConversationsFromFirestore(userId);
    },
    enabled: !!userId, // Only execute if userId is present
    staleTime: 30 * 1000, // 30 seconds
  });
}

/**
 * Mutation to create a new conversation
 *
 * Features:
 * - Optimistic update (adds to cache immediately)
 * - Automatic rollback on error
 * - Invalidates and refetches after success
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

      // Optimistic update: add temporary conversation
      queryClient.setQueryData<SavedConversation[]>(
        conversationKeys.byUser(userId || ""),
        (old) => {
          const tempConv: SavedConversation = {
            id: "temp-" + Date.now(),
            userId: userId || "",
            name: newConversation.name,
            timestamp: new Date().toLocaleString("en-US"),
            history: newConversation.history,
          };
          return [tempConv, ...(old || [])];
        }
      );

      return { previousConversations };
    },

    // Rollback on error
    onError: (err, newConversation, context) => {
      console.error("❌ Error creating conversation:", err);
      if (context?.previousConversations) {
        queryClient.setQueryData(
          conversationKeys.byUser(userId || ""),
          context.previousConversations
        );
      }
    },

    // Refetch after success
    onSuccess: (data) => {
      console.log("✅ Conversation created:", data.id);
      queryClient.invalidateQueries({
        queryKey: conversationKeys.byUser(userId || ""),
      });
    },
  });
}

/**
 * Mutation to update conversation name
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
 * Mutation to update conversation history (auto-save)
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

    // Refetch per mostrare la conversazione aggiornata nella lista
    onSuccess: (_, variables) => {
      console.log("✅ Conversation history updated:", variables.id);
      // Invalidate and refetch to update the sidebar list
      queryClient.invalidateQueries({
        queryKey: conversationKeys.byUser(userId || ""),
      });
    },
  });
}

/**
 * Mutation to delete a conversation
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
