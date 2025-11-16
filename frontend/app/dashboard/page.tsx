"use client";

import { useRef, useEffect, FormEvent, useState } from "react";
import { Loader } from "lucide-react";
import type { Message } from "ai/react";
import type { SavedConversation } from "@/lib/types";
import { useTheme } from "@/hooks/useTheme";
import { useUserId } from "@/hooks/useUserId";
import { useDocumentUpload } from "@/hooks/useDocumentUpload";
import { useDocumentStatus } from "@/hooks/useDocumentStatus";
import { useDocuments } from "@/hooks/useDocuments";
import { useChatAI } from "@/hooks/useChatAI";
import { Sidebar } from "@/components/Sidebar";
import { RightSidebar } from "@/components/RightSidebar";
import { TopBar } from "@/components/TopBar";
import { ChatSection } from "@/components/ChatSection";
import { UploadModal } from "@/components/UploadModal";
import { RenameModal } from "@/components/RenameModal";
import { ConfirmModal } from "@/components/ConfirmModal";
import ProtectedRoute from "@/components/ProtectedRoute";

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
  const [leftSidebarOpen, setLeftSidebarOpen] = useState(false);
  const [rightSidebarOpen, setRightSidebarOpen] = useState(false);
  const [uploadModalOpen, setUploadModalOpen] = useState(false);

  const { 
    file, 
    handleFileChange, 
    handleUpload, 
    isUploading, 
    uploadAlert,
    resetAlert,
  } = useDocumentUpload();

  // Document management
  const {
    documents,
    isLoading: isLoadingDocuments,
    refreshDocuments,
    deleteDocument,
  } = useDocuments(userId);

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

  const submitUpload = async (e: FormEvent) => {
    if (userId) {
      await handleUpload(e, userId);
      // Refresh documents list and close modal on success
      await refreshDocuments();
      setUploadModalOpen(false);
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
      <div className="h-screen flex flex-col bg-gray-100 dark:bg-gray-900 font-sans transition-colors duration-500">
        {/* Top Bar */}
        <TopBar
          onOpenLeftSidebar={() => setLeftSidebarOpen(true)}
          onOpenRightSidebar={() => setRightSidebarOpen(true)}
          onNewConversation={handleNewConversation}
          hasConversation={chatHistory.length > 0}
        />

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

        {/* Main content area - grows to fill remaining space */}
        <div className="flex flex-1 overflow-hidden">
          {/* Left Sidebar - Documents & Conversations */}
          <Sidebar
            userId={userId}
            savedConversations={savedConversations}
            mobileOpen={leftSidebarOpen}
            onCloseMobile={() => setLeftSidebarOpen(false)}
            onLoadConversation={handleLoad}
            onDeleteConversation={handleDelete}
            onRenameConversation={handleRename}
          />

          {/* Chat area - takes remaining space */}
          <div className="flex-1 flex flex-col p-2 sm:p-4 lg:p-6 overflow-hidden">
            <ChatSection
              chatHistory={chatHistory}
              query={input}
              isQuerying={isLoading}
              userId={userId}
              chatEndRef={chatEndRef}
              onQueryChange={handleQueryChange}
              onQuerySubmit={submitQuery}
              hasDocuments={hasDocuments}
              isCheckingDocuments={isChecking}
              onOpenUploadModal={() => setUploadModalOpen(true)}
            />
          </div>

          {/* Right Sidebar - User Profile & Settings */}
          <RightSidebar
            userId={userId}
            theme={theme}
            mobileOpen={rightSidebarOpen}
            onCloseMobile={() => setRightSidebarOpen(false)}
            onToggleTheme={toggleTheme}
            documents={documents}
            isLoadingDocuments={isLoadingDocuments}
            statusAlert={statusAlert}
            onDeleteDocument={deleteDocument}
            onRefreshDocuments={refreshDocuments}
          />
        </div>

        {/* Upload Modal */}
        <UploadModal
          isOpen={uploadModalOpen}
          onClose={() => {
            setUploadModalOpen(false);
            resetAlert();
          }}
          file={file}
          isUploading={isUploading}
          uploadAlert={uploadAlert}
          onFileChange={handleFileChange}
          onUpload={submitUpload}
        />
      </div>
    </ProtectedRoute>
  );
}
