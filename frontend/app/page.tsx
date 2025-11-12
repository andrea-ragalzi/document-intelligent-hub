"use client";

import { useRef, useEffect, FormEvent } from "react";
import { Sun, Moon, Loader } from "lucide-react";
import type { Message } from "ai/react";
import type { SavedConversation } from "@/lib/types";
import { useTheme } from "@/hooks/useTheme";
import { useUserId } from "@/hooks/useUserId";
import { useDocumentUpload } from "@/hooks/useDocumentUpload";
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

  const {
    chatHistory,
    input,
    handleInputChange,
    handleSubmit,
    isLoading,
    setMessages,
  } = useChatAI({ userId: userId || "" });

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

  // TanStack Query - gestisce le conversazioni con Firestore
  const { data: savedConversations = [], isLoading: _isLoadingConversations } =
    useConversationsQuery(userId);

  const createConversation = useCreateConversation(userId);
  const updateConversationName = useUpdateConversationName(userId);
  const updateConversationHistory = useUpdateConversationHistory(userId);
  const deleteConversation = useDeleteConversation(userId);

  const isSavingRef = useRef(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Genera un nome automatico per la conversazione
  const generateConversationName = (): string => {
    if (chatHistory.length > 0) {
      const firstUserMessage = chatHistory.find((msg) => msg.type === "user");
      if (firstUserMessage) {
        // Prendi le prime 50 caratteri del primo messaggio
        const preview = firstUserMessage.text.substring(0, 50);
        return preview.length < firstUserMessage.text.length
          ? `${preview}...`
          : preview;
      }
    }
    // Fallback: usa data e ora
    return `Conversazione del ${new Date().toLocaleString("it-IT")}`;
  };

  // Auto-scroll quando cambia la chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatHistory]);

  // Salvataggio automatico della conversazione
  useEffect(() => {
    // Salva SOLO quando l'assistente finisce di rispondere
    // cioè quando isLoading passa da true a false
    if (isLoading) {
      // Assistente sta ancora scrivendo, non salvare
      return;
    }

    // Non salvare se:
    // - Non c'è userId
    // - La chat è vuota
    // - Stiamo già salvando
    if (!userId || chatHistory.length === 0 || isSavingRef.current) {
      return;
    }

    // Salva solo se c'è almeno una coppia domanda-risposta completa
    if (chatHistory.length < 2) {
      return;
    }

    // Salva solo se ci sono nuovi messaggi
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
      startSaving();
      console.log("💾 Auto-saving conversation...");
      console.log("  Messages:", chatHistory.length);
      console.log("  Current ID:", currentConversationId);
      console.log("  Last saved count:", lastSavedMessageCount);

      try {
        if (currentConversationId) {
          // Aggiorna conversazione esistente
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
          // Crea nuova conversazione
          const autoName = generateConversationName();
          console.log("📝 Creating new conversation:", autoName);
          await createConversation.mutateAsync({
            name: autoName,
            history: chatHistory.map((msg) => ({
              type: msg.type as "user" | "assistant",
              text: msg.text,
              sources: msg.sources || [],
            })),
          });
          console.log(
            "✅ New conversation created, waiting for state update..."
          );
          // L'ID verrà impostato dal secondo useEffect
        }
      } catch (error) {
        console.error("❌ Auto-save failed:", error);
      } finally {
        isSavingRef.current = false;
        finishSaving();
      }
    };

    // Debounce di 500ms per evitare salvataggi multipli
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
  ]);

  // Intercetta quando viene creata una nuova conversazione e imposta l'ID
  useEffect(() => {
    // Se non abbiamo un ID conversazione, ma abbiamo delle conversazioni salvate,
    // e l'ultima conversazione ha lo stesso numero di messaggi della chat corrente,
    // significa che è quella che abbiamo appena creato
    if (
      !currentConversationId &&
      savedConversations.length > 0 &&
      chatHistory.length >= 2
    ) {
      const newestConv = savedConversations[0];
      // Verifica che la conversazione più recente abbia lo stesso numero di messaggi
      if (newestConv.history.length === chatHistory.length) {
        console.log("🆔 Setting conversation ID:", newestConv.id);
        setCurrentConversation(newestConv.id);
        updateSavedMessageCount(chatHistory.length);
      }
    }
  }, [
    savedConversations,
    currentConversationId,
    chatHistory.length,
    setCurrentConversation,
    updateSavedMessageCount,
  ]);

  const ThemeIcon = theme === "light" ? Moon : Sun;

  const handleLoad = (conv: SavedConversation) => {
    console.log("📂 Loading conversation:", conv.name);
    console.log("  Messages:", conv.history.length);

    // Converti da ChatMessage a Message (formato Vercel AI)
    const convertedMessages: Message[] = conv.history.map((msg, index) => ({
      id: `loaded-${conv.id}-${index}`,
      role: msg.type === "user" ? "user" : "assistant",
      content: msg.text,
    }));

    // Usa setMessages per caricare i messaggi nella chat
    setMessages(convertedMessages);

    // Imposta questa come conversazione corrente
    setCurrentConversation(conv.id);
    updateSavedMessageCount(conv.history.length);

    setStatusAlert({
      message: `Conversazione "${conv.name}" caricata (${conv.history.length} messaggi).`,
      type: "success",
    });
  };

  const handleDelete = async (id: string, name: string) => {
    // Apri il modal di conferma
    openDeleteModal(id, name);
  };

  const confirmDelete = async () => {
    if (!conversationToDelete) return;

    const { id, name } = conversationToDelete;
    console.log("🗑️ Eliminazione confermata, procedendo...");

    try {
      await deleteConversation.mutateAsync(id);

      // Se stiamo eliminando la conversazione corrente, reset
      if (id === currentConversationId) {
        resetConversation();
      }

      setStatusAlert({
        message: `Conversazione "${name}" eliminata.`,
        type: "success",
      });
    } catch {
      setStatusAlert({
        message: `Errore durante l'eliminazione di "${name}".`,
        type: "error",
      });
    }

    // Chiudi il modal
    closeDeleteModal();
  };

  const cancelDelete = () => {
    console.log("❌ Eliminazione annullata dall'utente");
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
        message: `Conversazione rinominata in "${newName}".`,
        type: "success",
      });
      closeRenameModal();
      return true;
    } catch {
      setStatusAlert({
        message: `Errore durante la rinomina.`,
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
      message: "Nuova conversazione iniziata.",
      type: "info",
    });
  };

  const submitQuery = (e: FormEvent) => {
    e.preventDefault();
    if (userId) {
      handleSubmit(e);
    } else {
      setStatusAlert({
        message: "Impossibile inviare: ID Utente non disponibile.",
        type: "error",
      });
    }
  };

  // Wrapper per handleInputChange per compatibilità con ChatSection
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
        message: "Impossibile caricare: ID Utente non disponibile.",
        type: "error",
      });
    }
  };

  if (!isAuthReady) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-100 dark:bg-gray-900">
        <Loader className="animate-spin mr-2" size={24} /> Caricamento...
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
          title="Elimina Conversazione"
          message={`Sei sicuro di voler eliminare la conversazione "${conversationToDelete?.name}"?\n\nQuesta azione non può essere annullata.`}
          confirmText="Elimina"
          cancelText="Annulla"
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
          />
        </div>
      </div>
    </ProtectedRoute>
  );
}
