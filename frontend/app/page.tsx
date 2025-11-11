'use client';

import { useState, useRef, useEffect, FormEvent } from 'react';
import { Sun, Moon, Loader } from 'lucide-react';
import type { AlertState, SavedConversation } from '@/lib/types';
import { useTheme } from '@/hooks/useTheme';
import { useUserId } from '@/hooks/useUserId';
import { useConversations } from '@/hooks/useConversations';
import { useDocumentUpload } from '@/hooks/useDocumentUpload';
import { useChatAI } from '@/hooks/useChatAI';
import { Sidebar } from '@/components/Sidebar';
import { ChatSection } from '@/components/ChatSection';
import { SaveModal } from '@/components/SaveModal';

export default function Page() {
  const { theme, toggleTheme } = useTheme();
  const { userId, isAuthReady } = useUserId();
  const { file, handleFileChange, handleUpload, isUploading, uploadAlert } = useDocumentUpload();
  const { chatHistory, input, handleInputChange, handleSubmit, isLoading } = useChatAI({ userId: userId || '' });
  const { savedConversations, saveConversation, deleteConversation } = useConversations(chatHistory);

  const [saveModalOpen, setSaveModalOpen] = useState(false);
  const [conversationName, setConversationName] = useState('');
  const [statusAlert, setStatusAlert] = useState<AlertState | null>(null);

  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory]);

  const ThemeIcon = theme === 'light' ? Moon : Sun;

  const handleSave = async (e: FormEvent) => {
    e.preventDefault();
    if (!conversationName.trim()) {
      setStatusAlert({ message: 'Inserisci un nome valido per la conversazione.', type: 'error' });
      return;
    }

    const success = saveConversation(conversationName.trim());
    if (success) {
      setStatusAlert({
        message: `Conversazione "${conversationName.trim()}" salvata con successo!`,
        type: 'success'
      });
      setSaveModalOpen(false);
      setConversationName('');
    } else {
      setStatusAlert({ message: 'Errore durante il salvataggio della conversazione.', type: 'error' });
    }
  };

  const handleLoad = (_conv: SavedConversation) => {
    // Con useChat di Vercel AI, non possiamo più sostituire direttamente la cronologia
    // Questa funzionalità richiede un refactor più profondo
    setStatusAlert({
      message: `Il caricamento delle conversazioni sarà implementato in futuro.`,
      type: 'info'
    });
  }; const handleDelete = async (id: string, name: string) => {
    const success = deleteConversation(id);
    if (success) {
      setStatusAlert({ message: `Conversazione "${name}" eliminata.`, type: 'success' });
    } else {
      setStatusAlert({ message: `Errore durante l'eliminazione di "${name}".`, type: 'error' });
    }
  };

  const submitQuery = (e: FormEvent) => {
    e.preventDefault();
    if (userId) {
      handleSubmit(e);
    } else {
      setStatusAlert({ message: 'Impossibile inviare: ID Utente non disponibile.', type: 'error' });
    }
  };

  // Wrapper per handleInputChange per compatibilità con ChatSection
  const handleQueryChange = (value: string) => {
    handleInputChange({ target: { value } } as React.ChangeEvent<HTMLInputElement>);
  };

  const submitUpload = (e: FormEvent) => {
    if (userId) {
      handleUpload(e, userId);
    } else {
      setStatusAlert({ message: 'Impossibile caricare: ID Utente non disponibile.', type: 'error' });
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
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900 font-sans p-4 sm:p-6 lg:p-10 flex justify-center transition-colors duration-500">
      <button
        onClick={toggleTheme}
        aria-label="Toggle dark mode"
        className="fixed top-4 right-4 z-50 p-2 rounded-full bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 shadow-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition duration-300"
      >
        <ThemeIcon size={20} />
      </button>

      <SaveModal
        isOpen={saveModalOpen}
        conversationName={conversationName}
        setConversationName={setConversationName}
        onClose={() => setSaveModalOpen(false)}
        onSave={handleSave}
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
        />

        <ChatSection
          chatHistory={chatHistory}
          query={input}
          isQuerying={isLoading}
          userId={userId}
          chatEndRef={chatEndRef}
          onQueryChange={handleQueryChange}
          onQuerySubmit={submitQuery}
          onSaveClick={() => setSaveModalOpen(true)}
        />
      </div>
    </div>
  );
}
