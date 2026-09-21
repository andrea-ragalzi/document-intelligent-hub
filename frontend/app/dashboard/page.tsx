"use client";

import { useRef, useEffect, FormEvent, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Loader } from "lucide-react";
import {
  EmailAuthProvider,
  GoogleAuthProvider,
  reauthenticateWithCredential,
  reauthenticateWithPopup,
} from "firebase/auth";
import type { SavedConversation } from "@/lib/types";
import { toAiSdkMessages } from "@/lib/chatMessagePersistence";
import { deleteAccountData } from "@/lib/accountDataCleanup";
import { rethrowAccountDeletionFailure } from "@/lib/accountDeletionErrors";
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
import { BugReportModal } from "@/components/BugReportModal";
import { FeedbackModal } from "@/components/FeedbackModal";
import AccountProvisioningModal from "@/components/AccountProvisioningModal";
import { ServerOfflineBanner } from "@/components/ServerOfflineBanner";
import ProtectedRoute from "@/components/ProtectedRoute";
import { useAuth } from "@/contexts/AuthContext";
import { useServerStatus } from "@/hooks/useServerStatus";
import { useUserTier } from "@/hooks/useUserTier";
import { useQueryUsage } from "@/hooks/useQueryUsage";
import { useDemoDocument } from "@/hooks/useDemoDocument";
import { getDemoDocumentVisibility } from "@/lib/demoDocumentVisibility";
import { useVisualViewportHeight } from "@/hooks/useVisualViewportHeight";

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
  const dashboardViewportRef = useRef<HTMLDivElement>(null);
  useVisualViewportHeight(dashboardViewportRef);
  const router = useRouter();
  const { theme, toggleTheme } = useTheme();
  const { userId, isAuthReady } = useUserId();
  const { user } = useAuth();
  const { tier, limits: tierLimits, isLoading: isTierLoading, refreshTier } = useUserTier();
  const { queriesUsed, isLimitReached, refetch: refetchQueryUsage } = useQueryUsage();
  const [leftSidebarOpen, setLeftSidebarOpen] = useState(false);
  const [rightSidebarOpen, setRightSidebarOpen] = useState(false);
  const [uploadModalOpen, setUploadModalOpen] = useState(false);
  const [deleteAccountModalOpen, setDeleteAccountModalOpen] = useState(false);
  const [accountProvisioningModalOpen, setAccountProvisioningModalOpen] = useState(false);

  // Document management
  const {
    documents: rawDocuments,
    isLoading: isLoadingDocuments,
    refreshDocuments,
    deleteDocument,
    previewDocument,
    downloadDocument,
  } = useDocuments(userId);

  // Ensure documents is always an array
  const documents = rawDocuments || [];

  const {
    files,
    isUploading,
    uploadAlert,
    handleFileChange,
    handleUpload,
    pendingDuplicate,
    resolveDuplicate,
    resetAlert,
    documentsUploaded: _documentsUploaded,
  } = useDocumentUpload({
    isUnlimited: tier === "UNLIMITED",
    onSuccess: () => {
      void refreshDocuments();
      setUploadModalOpen(false);
      resetAlert();
    },
  });

  // Check if user has uploaded documents
  const { hasDocuments, isChecking, refreshDocumentStatus } = useDocumentStatus(userId);

  const handleDemoDocumentReady = useCallback(async () => {
    const [, statusRefreshed] = await Promise.all([refreshDocuments(), refreshDocumentStatus()]);
    return statusRefreshed;
  }, [refreshDocuments, refreshDocumentStatus]);
  const { state: demoDocumentState, suggestedQuestions } = useDemoDocument({
    userId,
    onReady: handleDemoDocumentReady,
  });
  const visibleDemoDocument = getDemoDocumentVisibility(
    documents,
    demoDocumentState,
    suggestedQuestions
  );

  // Server status monitoring
  const {
    isOnline: isServerOnline,
    isChecking: isCheckingServer,
    checkStatus: retryServerConnection,
  } = useServerStatus();

  // Zustand UI Store - sostituisce tutti gli useState
  const {
    statusAlert: _statusAlert,
    setStatusAlert,
    renameModalOpen,
    conversationToRename,
    currentConversationId,
    lastSavedMessageCount,
    isSaving: _isSaving,
    bugReportModalOpen,
    feedbackModalOpen,
    isServerOnline: _isServerOnlineStore,
    serverOfflineBannerDismissed,
    openRenameModal,
    closeRenameModal,
    openBugReportModal,
    closeBugReportModal,
    openFeedbackModal,
    closeFeedbackModal,
    setCurrentConversation,
    updateSavedMessageCount,
    startSaving,
    finishSaving,
    resetConversation,
    setServerOnline,
  } = useUIStore();

  // Sync server status to store
  useEffect(() => {
    setServerOnline(isServerOnline);
  }, [isServerOnline, setServerOnline]);

  // Refresh documents when server comes back online
  useEffect(() => {
    // Only refresh if server changed from offline to online (not on initial mount)
    if (isServerOnline && !previousServerStatusRef.current && userId) {
      refreshDocuments();
      // Also trigger document status refresh
      globalThis.dispatchEvent(new Event("refreshDocumentStatus"));
    }
    // Update previous status
    previousServerStatusRef.current = isServerOnline;
  }, [isServerOnline, userId, refreshDocuments]);

  const { chatHistory, input, handleInputChange, handleSubmit, isLoading, setMessages } = useChatAI(
    {
      userId: userId || "",
    }
  );

  // TanStack Query - gestisce le conversazioni con Firestore
  const { data: savedConversations = [], isLoading: _isLoadingConversations } =
    useConversationsQuery(userId);

  const createConversation = useCreateConversation(userId);
  const updateConversationName = useUpdateConversationName(userId);
  const updateConversationHistory = useUpdateConversationHistory(userId);
  const deleteConversation = useDeleteConversation(userId);

  const isSavingRef = useRef(false);
  const previousServerStatusRef = useRef<boolean>(true); // Track previous server status

  // Track if we're waiting for a conversation to be created
  const isCreatingConversationRef = useRef(false);

  // Generate automatic name for the conversation
  const generateConversationName = (): string => {
    if (chatHistory.length > 0) {
      const firstUserMessage = chatHistory.find(msg => msg.type === "user");
      if (firstUserMessage) {
        // Take first 50 characters of the first message
        const preview = firstUserMessage.text.substring(0, 50);
        return preview.length < firstUserMessage.text.length ? `${preview}...` : preview;
      }
    }
    // Fallback: use date and time
    return `Conversation from ${new Date().toLocaleString("en-US")}`;
  };

  // Auto-scroll is now handled by ChatSection component's useChatScroll hook

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
      return;
    }

    const autoSave = async () => {
      isSavingRef.current = true;
      isCreatingConversationRef.current = true;
      startSaving();

      try {
        if (currentConversationId) {
          // Update existing conversation
          await updateConversationHistory.mutateAsync({
            id: currentConversationId,
            history: chatHistory.map(msg => ({
              type: msg.type,
              text: msg.text,
              sources: msg.sources || [],
            })),
          });
          updateSavedMessageCount(chatHistory.length);
        } else {
          // Create new conversation
          const autoName = generateConversationName();
          const newConversation = await createConversation.mutateAsync({
            name: autoName,
            history: chatHistory.map(msg => ({
              type: msg.type,
              text: msg.text,
              sources: msg.sources || [],
            })),
          });
          // Set the conversation ID immediately
          setCurrentConversation(newConversation.id);
          updateSavedMessageCount(chatHistory.length);
        }
      } catch {
        console.error("Conversation auto-save failed.");
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

  // Provision a tier on first login when Firebase has not issued a claim yet.
  useEffect(() => {
    if (!isTierLoading && user && tier === "FREE") {
      // Check if user has custom claims set
      user.getIdTokenResult().then(tokenResult => {
        // If no tier claim exists, show account provisioning.
        if (!tokenResult.claims.tier) {
          setAccountProvisioningModalOpen(true);
        }
      });
    }
  }, [user, tier, isTierLoading]);

  const handleLoad = (conv: SavedConversation) => {
    // Restore Firestore source metadata as AI SDK annotations for rendering.
    const convertedMessages = toAiSdkMessages(conv.id, conv.history);

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
    // If we're deleting the current conversation, clear chat BEFORE deleting
    const isDeletingCurrentConversation = id === currentConversationId;
    if (isDeletingCurrentConversation) {
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
    openRenameModal(id, currentName);
  };

  const handlePinConversation = async (id: string, isPinned: boolean) => {
    try {
      // Trova la conversazione da aggiornare
      const conversation = savedConversations.find(conv => conv.id === id);
      if (!conversation) {
        throw new Error("Conversation not found");
      }

      // Update Firestore con il nuovo stato isPinned
      await updateConversationHistory.mutateAsync({
        id,
        history: conversation.history,
        metadata: {
          isPinned,
        },
      });

      setStatusAlert({
        message: isPinned ? "Conversation pinned to top." : "Conversation unpinned.",
        type: "success",
      });
    } catch {
      console.error("Unable to update the conversation pin state.");
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
      // Refresh query usage counter after submission
      // The counter will update when the response comes back
      setTimeout(() => {
        refetchQueryUsage();
      }, 1000);
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
      await handleUpload(
        e,
        userId,
        documents.map(document => document.filename)
      );
    } else {
      setStatusAlert({
        message: "Cannot upload: User ID not available.",
        type: "error",
      });
    }
  };

  const requiresPasswordForDeletion = Boolean(
    user?.providerData.some(provider => provider.providerId === "password")
  );

  const handleDeleteAccount = async (password?: string) => {
    if (!user || !userId) return;

    try {
      // Firebase only permits account deletion shortly after authentication.
      // Reauthenticate before cleanup so we never remove server data and then
      // discover that the Firebase identity cannot be removed.
      if (requiresPasswordForDeletion) {
        if (!user.email || !password) {
          throw new Error("Enter your password to delete your account.");
        }
        await reauthenticateWithCredential(
          user,
          EmailAuthProvider.credential(user.email, password)
        );
      } else if (user.providerData.some(provider => provider.providerId === "google.com")) {
        await reauthenticateWithPopup(user, new GoogleAuthProvider());
      } else {
        throw new Error("Please sign in again, then retry account deletion.");
      }

      const idToken = await user.getIdToken(true);
      await deleteAccountData(idToken);
      await user.delete();
      router.push("/login");
    } catch (error) {
      rethrowAccountDeletionFailure(error);
    }
  };

  if (!isAuthReady) {
    return (
      <div className="flex items-center justify-center h-screen bg-canvas text-muted">
        <Loader className="animate-spin mr-2" size={24} /> Loading...
      </div>
    );
  }

  return (
    <ProtectedRoute>
      <div
        ref={dashboardViewportRef}
        className="app-shell h-screen h-[100dvh] flex flex-col font-sans transition-colors duration-300"
      >
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
          tier={tier}
          isTierLoading={isTierLoading}
        />

        {/* Server Offline Banner */}
        {!isServerOnline && !serverOfflineBannerDismissed && (
          <ServerOfflineBanner onRetry={retryServerConnection} isRetrying={isCheckingServer} />
        )}

        <RenameModal
          isOpen={renameModalOpen}
          currentName={conversationToRename?.currentName || ""}
          onClose={closeRenameModal}
          onRename={handleRenameSubmit}
        />

        {/* Main content area - grows to fill remaining space */}
        <div className="flex min-h-0 flex-1 overflow-hidden">
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
          <div className="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden p-0 sm:p-4 lg:p-6">
            <ChatSection
              chatHistory={chatHistory}
              query={input}
              isQuerying={isLoading}
              userId={userId}
              onQueryChange={handleQueryChange}
              onQuerySubmit={submitQuery}
              hasDocuments={hasDocuments}
              isCheckingDocuments={isChecking}
              onOpenUploadModal={() => setUploadModalOpen(true)}
              isServerOnline={isServerOnline}
              isLimitReached={isLimitReached}
              demoDocumentState={visibleDemoDocument.state}
              suggestedQuestions={visibleDemoDocument.suggestedQuestions}
              onSuggestedQuestion={handleQueryChange}
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
              onPreviewDocument={previewDocument}
              onDownloadDocument={downloadDocument}
              onRefreshDocuments={refreshDocuments}
              onDeleteAccount={() => setDeleteAccountModalOpen(true)}
              onOpenBugReport={openBugReportModal}
              onOpenFeedback={openFeedbackModal}
              isServerOnline={isServerOnline}
              currentQueries={queriesUsed}
              tier={tier}
              tierLimits={tierLimits}
              isTierLoading={isTierLoading}
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
                onPreviewDocument={previewDocument}
                onDownloadDocument={downloadDocument}
                onRefreshDocuments={refreshDocuments}
                onDeleteAccount={() => setDeleteAccountModalOpen(true)}
                onOpenBugReport={openBugReportModal}
                onOpenFeedback={openFeedbackModal}
                isServerOnline={isServerOnline}
                currentQueries={queriesUsed}
                tier={tier}
                tierLimits={tierLimits}
                isTierLoading={isTierLoading}
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
          files={files}
          isUploading={isUploading}
          uploadAlert={uploadAlert}
          pendingDuplicate={pendingDuplicate}
          onFileChange={handleFileChange}
          onUpload={submitUpload}
          onResolveDuplicate={resolveDuplicate}
          isUnlimited={tier === "UNLIMITED"}
        />

        {/* Delete Account Modal */}
        <DeleteAccountModal
          isOpen={deleteAccountModalOpen}
          onClose={() => setDeleteAccountModalOpen(false)}
          onConfirm={handleDeleteAccount}
          userEmail={user?.email || ""}
          requiresPassword={requiresPasswordForDeletion}
        />

        {/* Bug Report Modal */}
        <BugReportModal
          isOpen={bugReportModalOpen}
          onClose={closeBugReportModal}
          conversationId={currentConversationId}
        />

        {/* Feedback Modal */}
        <FeedbackModal
          isOpen={feedbackModalOpen}
          onClose={closeFeedbackModal}
          conversationId={currentConversationId}
        />

        <AccountProvisioningModal
          isOpen={accountProvisioningModalOpen}
          onSuccess={_assignedTier => {
            // useRegistration already forced token refresh, so update tier immediately
            refreshTier();
            setAccountProvisioningModalOpen(false);
          }}
        />
      </div>
    </ProtectedRoute>
  );
}
