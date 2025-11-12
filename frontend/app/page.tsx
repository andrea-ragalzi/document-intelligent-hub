"use client";

import { useState, useRef, useEffect, FormEvent } from "react";
import { Sun, Moon, Loader } from "lucide-react";
import type { Message } from "ai/react";
import type { AlertState, SavedConversation } from "@/lib/types";
import { useTheme } from "@/hooks/useTheme";
import { useUserId } from "@/hooks/useUserId";
import { useConversations } from "@/hooks/useConversations";
import { useDocumentUpload } from "@/hooks/useDocumentUpload";
import { useChatAI } from "@/hooks/useChatAI";
import { Sidebar } from "@/components/Sidebar";
import { ChatSection } from "@/components/ChatSection";
import { RenameModal } from "@/components/RenameModal";
import { ConfirmModal } from "@/components/ConfirmModal";
import ProtectedRoute from "@/components/ProtectedRoute";
import UserProfile from "@/components/UserProfile";

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
  const {
    savedConversations,
    saveConversation,
    deleteConversation,
    updateConversationName,
    updateConversationHistory,
  } = useConversations({ currentChatHistory: chatHistory, userId });

  const [statusAlert, setStatusAlert] = useState<AlertState | null>(null);
  const [renameModalOpen, setRenameModalOpen] = useState(false);
  const [conversationToRename, setConversationToRename] = useState<{
    id: string;
    currentName: string;
  } | null>(null);
  const [confirmDeleteOpen, setConfirmDeleteOpen] = useState(false);
  const [conversationToDelete, setConversationToDelete] = useState<{
    id: string;
    name: string;
  } | null>(null);
  const [currentConversationId, setCurrentConversationId] = useState<
    string | null
  >(null);
  const [lastSavedMessageCount, setLastSavedMessageCount] = useState(0);
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
      console.log("💾 Auto-saving conversation...");
      console.log("  Messages:", chatHistory.length);
      console.log("  Current ID:", currentConversationId);
      console.log("  Last saved count:", lastSavedMessageCount);

      try {
        if (currentConversationId) {
          // Aggiorna conversazione esistente
          const success = await updateConversationHistory(
            currentConversationId,
            chatHistory
          );
          if (success) {
            console.log("✅ Conversation updated, updating counter");
            setLastSavedMessageCount(chatHistory.length);
          } else {
            console.log("❌ Update failed");
          }
        } else {
          // Crea nuova conversazione solo se non esiste già
          const autoName = generateConversationName();
          console.log("📝 Creating new conversation:", autoName);
          const success = await saveConversation(autoName);
          if (success) {
            console.log(
              "✅ New conversation created, waiting for state update..."
            );
            // Non impostiamo lastSavedMessageCount qui, lo farà il secondo useEffect
          } else {
            console.log("❌ Save failed");
          }
        }
      } catch (error) {
        console.error("❌ Auto-save failed:", error);
      } finally {
        isSavingRef.current = false;
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
    saveConversation,
    generateConversationName,
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
        setCurrentConversationId(newestConv.id);
        setLastSavedMessageCount(chatHistory.length);
      }
    }
  }, [savedConversations, currentConversationId, chatHistory.length]);

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
    setCurrentConversationId(conv.id);
    setLastSavedMessageCount(conv.history.length);

    setStatusAlert({
      message: `Conversazione "${conv.name}" caricata (${conv.history.length} messaggi).`,
      type: "success",
    });
  };

  const handleDelete = async (id: string, name: string) => {
    // Apri il modal di conferma
    setConversationToDelete({ id, name });
    setConfirmDeleteOpen(true);
  };

  const confirmDelete = async () => {
    if (!conversationToDelete) return;

    const { id, name } = conversationToDelete;
    console.log("🗑️ Eliminazione confermata, procedendo...");

    const success = await deleteConversation(id);
    if (success) {
      // Se stiamo eliminando la conversazione corrente, reset
      if (id === currentConversationId) {
        setCurrentConversationId(null);
        setLastSavedMessageCount(0);
      }
      setStatusAlert({
        message: `Conversazione "${name}" eliminata.`,
        type: "success",
      });
    } else {
      setStatusAlert({
        message: `Errore durante l'eliminazione di "${name}".`,
        type: "error",
      });
    }

    // Chiudi il modal
    setConfirmDeleteOpen(false);
    setConversationToDelete(null);
  };

  const cancelDelete = () => {
    console.log("❌ Eliminazione annullata dall'utente");
    setConfirmDeleteOpen(false);
    setConversationToDelete(null);
  };

  const handleRename = (id: string, currentName: string) => {
    console.log("✏️ Opening rename modal for:", id, currentName);
    setConversationToRename({ id, currentName });
    setRenameModalOpen(true);
  };

  const handleRenameSubmit = async (newName: string): Promise<boolean> => {
    if (!conversationToRename) return false;

    const success = await updateConversationName(
      conversationToRename.id,
      newName
    );

    if (success) {
      setStatusAlert({
        message: `Conversazione rinominata in "${newName}".`,
        type: "success",
      });
      setRenameModalOpen(false);
      setConversationToRename(null);
    } else {
      setStatusAlert({
        message: `Errore durante la rinomina.`,
        type: "error",
      });
    }

    return success;
  };

  const handleNewConversation = () => {
    console.log("🆕 Starting new conversation");
    setMessages([]);
    setCurrentConversationId(null);
    setLastSavedMessageCount(0);
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
          onClose={() => {
            setRenameModalOpen(false);
            setConversationToRename(null);
          }}
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
