"use client";

import { useRef, useEffect, FormEvent } from "react";
import { Sun, Moon, Loader } from "lucide-react";
import type { Message } from "ai/react";
import type { SavedConversation } from "@/lib/types";
import { useTheme } from "@/hooks/useTheme";
import { useUserId } from "@/hooks/useUserId";
import { useDocumentUpload } from "@/hooks/useDocumentUpload";
import { useDocumentStatus } from "@/hooks/useDocumentStatus";
import { useChatAI } from "@/hooks/useChatAI";
import { Sidebar } from "@/components/Sidebar";
import { ChatSection } from "@/components/ChatSection";
import { RenameModal } from "@/components/RenameModal";
import { ConfirmModal } from "@/components/ConfirmModal";
import ProtectedRoute from "@/components/ProtectedRoute";
import UserProfile from "@/components/UserProfile";

// Zustand store e TanStack Query
import { useUIStore } from "@/stores/uiStore";
import {
  useConversationsQuery,
  useCreateConversation,
  useUpdateConversationName,
  useUpdateConversationHistory,
  useDeleteConversation,
} from "@/hooks/queries/useConversationsQuery";

export default function Page() {
  const { theme, toggleTheme } = useTheme();
  const { userId, isAuthReady } = useUserId();
  const { file, handleFileChange, handleUpload, isUploading, uploadAlert } =
    useDocumentUpload();

  // Check if user has uploaded documents
  const { hasDocuments, isChecking } = useDocumentStatus(userId);

  // Zustand UI Store - sostituisce tutti gli useState
  const {
    statusAlert,
    setStatusAlert,
    renameModalOpen,
    confirmDeleteOpen,
    conversationToRename,
    conversationToDelete,
    currentConversationId,
    lastSavedMessageCount,
    isSaving: _isSaving,
    openRenameModal,
    closeRenameModal,
    openDeleteModal,
    closeDeleteModal,
    setCurrentConversation,
    updateSavedMessageCount,
    startSaving,
    finishSaving,
    resetConversation,
  } = useUIStore();

  const {
    chatHistory,
    input,
    handleInputChange,
    handleSubmit,
    isLoading,
    setMessages,
  } = useChatAI({
    userId: userId || "",
  });

  // TanStack Query - gestisce le conversazioni con Firestore
  const { data: savedConversations = [], isLoading: _isLoadingConversations } =
    useConversationsQuery(userId);

  const createConversation = useCreateConversation(userId);
  const updateConversationName = useUpdateConversationName(userId);
  const updateConversationHistory = useUpdateConversationHistory(userId);
  const deleteConversation = useDeleteConversation(userId);

  const isSavingRef = useRef(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Track if we're waiting for a conversation to be created
  const isCreatingConversationRef = useRef(false);

  // Generate automatic name for the conversation
  const generateConversationName = (): string => {
    if (chatHistory.length > 0) {
      const firstUserMessage = chatHistory.find((msg) => msg.type === "user");
      if (firstUserMessage) {
        // Take first 50 characters of the first message
        const preview = firstUserMessage.text.substring(0, 50);
        return preview.length < firstUserMessage.text.length
          ? `${preview}...`
          : preview;
      }
    }
    // Fallback: use date and time
    return `Conversation from ${new Date().toLocaleString("en-US")}`;
  };

  // Auto-scroll when chat changes
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatHistory]);

  // Automatic conversation save
  useEffect(() => {
    // Save ONLY when assistant finishes responding
    // i.e. when isLoading changes from true to false
    if (isLoading) {
      // Assistant is still writing, don't save
      return;
    }

    // Don't save if:
    // - No userId
    // - Chat is empty
    // - Already saving
    if (!userId || chatHistory.length === 0 || isSavingRef.current) {
      return;
    }

    // Only save if there's at least one complete question-answer pair
    if (chatHistory.length < 2) {
      return;
    }

    // Only save if there are new messages
    if (chatHistory.length <= lastSavedMessageCount) {
      console.log("⏭️ Skipping save - no new messages");
      console.log(
        "  Messages:",
        chatHistory.length,
        "Last saved:",
        lastSavedMessageCount
      );
      return;
    }

    const autoSave = async () => {
      isSavingRef.current = true;
      isCreatingConversationRef.current = true;
      startSaving();
      console.log("💾 Auto-saving conversation...");
      console.log("  Messages:", chatHistory.length);
      console.log("  Current ID:", currentConversationId);
      console.log("  Last saved count:", lastSavedMessageCount);

      try {
        if (currentConversationId) {
          // Update existing conversation
          await updateConversationHistory.mutateAsync({
            id: currentConversationId,
            history: chatHistory.map((msg) => ({
              type: msg.type as "user" | "assistant",
              text: msg.text,
              sources: msg.sources || [],
            })),
          });
          console.log("✅ Conversation updated, updating counter");
          updateSavedMessageCount(chatHistory.length);
        } else {
          // Create new conversation
          const autoName = generateConversationName();
          console.log("📝 Creating new conversation:", autoName);
          const newConversation = await createConversation.mutateAsync({
            name: autoName,
            history: chatHistory.map((msg) => ({
              type: msg.type as "user" | "assistant",
              text: msg.text,
              sources: msg.sources || [],
            })),
          });
          console.log(
            "✅ New conversation created with ID:",
            newConversation.id
          );
          // Set the conversation ID immediately
          setCurrentConversation(newConversation.id);
          updateSavedMessageCount(chatHistory.length);
        }
      } catch (error) {
        console.error("❌ Auto-save failed:", error);
      } finally {
        isSavingRef.current = false;
        isCreatingConversationRef.current = false;
        finishSaving();
      }
    };

    // 500ms debounce to avoid multiple saves
    const timeoutId = setTimeout(() => {
      autoSave();
    }, 500);

    return () => clearTimeout(timeoutId);
  }, [
    chatHistory,
    userId,
    isLoading,
    currentConversationId,
    lastSavedMessageCount,
    updateConversationHistory,
    createConversation,
    generateConversationName,
    startSaving,
    finishSaving,
    updateSavedMessageCount,
    setCurrentConversation,
  ]);

  const ThemeIcon = theme === "light" ? Moon : Sun;

  const handleLoad = (conv: SavedConversation) => {
    console.log("📂 Loading conversation:", conv.name);
    console.log("  Messages:", conv.history.length);

    // Convert from ChatMessage to Message (Vercel AI format)
    const convertedMessages: Message[] = conv.history.map((msg, index) => ({
      id: `loaded-${conv.id}-${index}`,
      role: msg.type === "user" ? "user" : "assistant",
      content: msg.text,
    }));

    // Use setMessages to load messages into chat
    setMessages(convertedMessages);

    // Set this as current conversation
    setCurrentConversation(conv.id);
    updateSavedMessageCount(conv.history.length);

    setStatusAlert({
      message: `Conversation "${conv.name}" loaded (${conv.history.length} messages).`,
      type: "success",
    });
  };

  const handleDelete = async (id: string, name: string) => {
    // Open confirmation modal
    openDeleteModal(id, name);
  };

  const confirmDelete = async () => {
    if (!conversationToDelete) return;

    const { id, name } = conversationToDelete;
    console.log("🗑️ Deletion confirmed, proceeding...");

    // If we're deleting the current conversation, clear chat BEFORE deleting
    const isDeletingCurrentConversation = id === currentConversationId;
    if (isDeletingCurrentConversation) {
      console.log("🧹 Clearing chat history for current conversation");
      setMessages([]); // Clear the chat history
      resetConversation(); // Reset the conversation state
      updateSavedMessageCount(0); // Reset saved message count
    }

    try {
      await deleteConversation.mutateAsync(id);

      setStatusAlert({
        message: `Conversation "${name}" deleted.`,
        type: "success",
      });
    } catch {
      setStatusAlert({
        message: `Error deleting "${name}".`,
        type: "error",
      });
    }

    // Close modal
    closeDeleteModal();
  };

  const cancelDelete = () => {
    console.log("❌ Deletion cancelled by user");
    closeDeleteModal();
  };

  const handleRename = (id: string, currentName: string) => {
    console.log("✏️ Opening rename modal for:", id, currentName);
    openRenameModal(id, currentName);
  };

  const handleRenameSubmit = async (newName: string): Promise<boolean> => {
    if (!conversationToRename) return false;

    try {
      await updateConversationName.mutateAsync({
        id: conversationToRename.id,
        newName,
      });

      setStatusAlert({
        message: `Conversation renamed to "${newName}".`,
        type: "success",
      });
      closeRenameModal();
      return true;
    } catch {
      setStatusAlert({
        message: `Error renaming conversation.`,
        type: "error",
      });
      return false;
    }
  };

  const handleNewConversation = () => {
    console.log("🆕 Starting new conversation");
    setMessages([]);
    resetConversation();
    setStatusAlert({
      message: "New conversation started.",
      type: "info",
    });
  };

  const submitQuery = (e: FormEvent) => {
    e.preventDefault();
    if (userId) {
      handleSubmit(e);
    } else {
      setStatusAlert({
        message: "Cannot send: User ID not available.",
        type: "error",
      });
    }
  };

  // Wrapper for handleInputChange for compatibility with ChatSection
  const handleQueryChange = (value: string) => {
    handleInputChange({
      target: { value },
    } as React.ChangeEvent<HTMLInputElement>);
  };

  const submitUpload = (e: FormEvent) => {
    if (userId) {
      handleUpload(e, userId);
    } else {
      setStatusAlert({
        message: "Cannot upload: User ID not available.",
        type: "error",
      });
    }
  };

  if (!isAuthReady) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-100 dark:bg-gray-900">
        <Loader className="animate-spin mr-2" size={24} /> Loading...
      </div>
    );
  }

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gray-100 dark:bg-gray-900 font-sans p-4 sm:p-6 lg:p-10 flex justify-center transition-colors duration-500">
        <div className="fixed top-4 right-4 z-50 flex items-center gap-2">
          <UserProfile />
          <button
            onClick={toggleTheme}
            aria-label="Toggle dark mode"
            className="p-2 rounded-full bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 shadow-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition duration-300"
          >
            <ThemeIcon size={20} />
          </button>
        </div>

        <RenameModal
          isOpen={renameModalOpen}
          currentName={conversationToRename?.currentName || ""}
          onClose={closeRenameModal}
          onRename={handleRenameSubmit}
        />

        <ConfirmModal
          isOpen={confirmDeleteOpen}
          title="Delete Conversation"
          message={`Are you sure you want to delete the conversation "${conversationToDelete?.name}"?\n\nThis action cannot be undone.`}
          confirmText="Delete"
          cancelText="Cancel"
          variant="danger"
          onConfirm={confirmDelete}
          onCancel={cancelDelete}
        />

        <div className="w-full max-w-7xl flex flex-col lg:flex-row gap-6">
          <Sidebar
            userId={userId}
            file={file}
            isUploading={isUploading}
            uploadAlert={uploadAlert}
            statusAlert={statusAlert}
            savedConversations={savedConversations}
            onFileChange={handleFileChange}
            onUpload={submitUpload}
            onLoadConversation={handleLoad}
            onDeleteConversation={handleDelete}
            onRenameConversation={handleRename}
          />

          <ChatSection
            chatHistory={chatHistory}
            query={input}
            isQuerying={isLoading}
            userId={userId}
            chatEndRef={chatEndRef}
            onQueryChange={handleQueryChange}
            onQuerySubmit={submitQuery}
            onNewConversation={handleNewConversation}
            hasDocuments={hasDocuments}
            isCheckingDocuments={isChecking}
          />
        </div>
      </div>
    </ProtectedRoute>
  );
}
