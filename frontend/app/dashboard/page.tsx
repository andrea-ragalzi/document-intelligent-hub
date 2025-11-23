"use client";

import { useRef, useEffect, FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
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
import { DeleteAccountModal } from "@/components/DeleteAccountModal";
import ProtectedRoute from "@/components/ProtectedRoute";
import { useAuth } from "@/contexts/AuthContext";

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
  const router = useRouter();
  const { theme, toggleTheme } = useTheme();
  const { userId, isAuthReady } = useUserId();
  const { user, logout } = useAuth();
  const [leftSidebarOpen, setLeftSidebarOpen] = useState(false);
  const [rightSidebarOpen, setRightSidebarOpen] = useState(false);
  const [uploadModalOpen, setUploadModalOpen] = useState(false);
  const [deleteAccountModalOpen, setDeleteAccountModalOpen] = useState(false);
  const [selectedOutputLanguage, setSelectedOutputLanguage] =
    useState<string>("en");

  const {
    file,
    isUploading,
    uploadAlert,
    handleFileChange,
    handleUpload,
    resetAlert,
    documentsUploaded: _documentsUploaded,
    selectedLanguage,
    setSelectedLanguage,
  } = useDocumentUpload({
    onSuccess: () => {
      setUploadModalOpen(false);
      resetAlert();
    },
  });

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
    statusAlert: _statusAlert,
    setStatusAlert,
    renameModalOpen,
    conversationToRename,
    currentConversationId,
    lastSavedMessageCount,
    isSaving: _isSaving,
    openRenameModal,
    closeRenameModal,
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
    selectedOutputLanguage,
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
    console.log("🗑️ Deleting conversation:", id, name);

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
  };

  const handleRename = (id: string, currentName: string) => {
    console.log("✏️ Opening rename modal for:", id, currentName);
    openRenameModal(id, currentName);
  };

  const handlePinConversation = async (id: string, isPinned: boolean) => {
    console.log(`📌 ${isPinned ? "Pinning" : "Unpinning"} conversation:`, id);

    try {
      // Trova la conversazione da aggiornare
      const conversation = savedConversations.find((conv) => conv.id === id);
      if (!conversation) {
        throw new Error("Conversation not found");
      }

      console.log("  Current isPinned state:", conversation.isPinned);
      console.log("  New isPinned state:", isPinned);
      console.log(
        "  Conversation history length:",
        conversation.history.length
      );

      // Update Firestore con il nuovo stato isPinned
      await updateConversationHistory.mutateAsync({
        id,
        history: conversation.history,
        metadata: {
          isPinned,
        },
      });

      console.log("✅ Pin state updated successfully in Firestore");

      setStatusAlert({
        message: isPinned
          ? "Conversation pinned to top."
          : "Conversation unpinned.",
        type: "success",
      });
    } catch (error) {
      console.error("❌ Error pinning conversation:", error);
      setStatusAlert({
        message: "Error updating conversation.",
        type: "error",
      });
    }
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

  const handleDeleteAccount = async () => {
    if (!user || !userId) return;

    try {
      // Delete all user data from Firestore (conversations and documents)
      const db = (await import("firebase/firestore")).getFirestore();
      const {
        collection,
        query: firestoreQuery,
        where,
        getDocs,
        deleteDoc,
      } = await import("firebase/firestore");

      // Delete all conversations
      const conversationsRef = collection(db, "conversations");
      const conversationsSnapshot = await getDocs(
        firestoreQuery(conversationsRef, where("userId", "==", userId))
      );

      const deletePromises = conversationsSnapshot.docs.map((doc) =>
        deleteDoc(doc.ref)
      );
      await Promise.all(deletePromises);

      // Delete user account from Firebase Auth
      await user.delete();

      // Redirect to login
      router.push("/login");
    } catch (error) {
      console.error("Error deleting account:", error);
      setStatusAlert({
        message: "Error deleting account. Please try again.",
        type: "error",
      });
    }
  };

  if (!isAuthReady) {
    return (
      <div className="flex items-center justify-center h-screen bg-indigo-50 dark:bg-indigo-950">
        <Loader className="animate-spin mr-2" size={24} /> Loading...
      </div>
    );
  }

  return (
    <ProtectedRoute>
      <div className="h-screen flex flex-col bg-indigo-50 dark:bg-indigo-950 font-sans transition-colors duration-500">
        {/* Top Bar */}
        <TopBar
          onOpenLeftSidebar={() => {
            setLeftSidebarOpen(true);
            setRightSidebarOpen(false);
          }}
          onOpenRightSidebar={() => {
            setRightSidebarOpen(true);
            setLeftSidebarOpen(false);
          }}
          onNewConversation={handleNewConversation}
          hasConversation={chatHistory.length > 0}
        />

        <RenameModal
          isOpen={renameModalOpen}
          currentName={conversationToRename?.currentName || ""}
          onClose={closeRenameModal}
          onRename={handleRenameSubmit}
        />

        {/* Main content area - grows to fill remaining space */}
        <div className="flex flex-1 overflow-hidden">
          {/* Left Sidebar - Always visible on desktop (lg+), toggle on mobile */}
          <div className="hidden lg:block">
            <Sidebar
              userId={userId}
              savedConversations={savedConversations}
              currentConversationId={currentConversationId}
              isOpen={true}
              onClose={() => {}}
              onNewConversation={handleNewConversation}
              onLoadConversation={handleLoad}
              onDeleteConversation={handleDelete}
              onRenameConversation={handleRename}
              onPinConversation={handlePinConversation}
            />
          </div>

          {/* Mobile Left Sidebar - Overlay mode */}
          {leftSidebarOpen && (
            <div className="lg:hidden">
              <Sidebar
                userId={userId}
                savedConversations={savedConversations}
                currentConversationId={currentConversationId}
                isOpen={leftSidebarOpen}
                onClose={() => setLeftSidebarOpen(false)}
                onNewConversation={handleNewConversation}
                onLoadConversation={handleLoad}
                onDeleteConversation={handleDelete}
                onRenameConversation={handleRename}
                onPinConversation={handlePinConversation}
              />
            </div>
          )}

          {/* Chat area - takes remaining space */}
          <div className="flex-1 flex flex-col p-0 sm:p-4 lg:p-6 overflow-hidden">
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
              selectedOutputLanguage={selectedOutputLanguage}
              onSelectOutputLanguage={setSelectedOutputLanguage}
            />
          </div>

          {/* Right Sidebar - Always visible on desktop (xl+), toggle on mobile */}
          <div className="hidden xl:block">
            <RightSidebar
              userId={userId}
              theme={theme}
              isOpen={true}
              onClose={() => {}}
              onToggleTheme={toggleTheme}
              documents={documents}
              isLoadingDocuments={isLoadingDocuments}
              onDeleteDocument={deleteDocument}
              onRefreshDocuments={refreshDocuments}
              onDeleteAccount={() => setDeleteAccountModalOpen(true)}
            />
          </div>

          {/* Mobile Right Sidebar - Overlay mode */}
          {rightSidebarOpen && (
            <div className="xl:hidden">
              <RightSidebar
                userId={userId}
                theme={theme}
                isOpen={rightSidebarOpen}
                onClose={() => setRightSidebarOpen(false)}
                onToggleTheme={toggleTheme}
                documents={documents}
                isLoadingDocuments={isLoadingDocuments}
                onDeleteDocument={deleteDocument}
                onRefreshDocuments={refreshDocuments}
                onDeleteAccount={() => setDeleteAccountModalOpen(true)}
              />
            </div>
          )}
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
          selectedLanguage={selectedLanguage}
          onLanguageChange={setSelectedLanguage}
        />

        {/* Delete Account Modal */}
        <DeleteAccountModal
          isOpen={deleteAccountModalOpen}
          onClose={() => setDeleteAccountModalOpen(false)}
          onConfirm={handleDeleteAccount}
          userEmail={user?.email || ""}
        />
      </div>
    </ProtectedRoute>
  );
}
