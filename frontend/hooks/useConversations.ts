'use client';

import { useState, useEffect, useCallback } from 'react';
import type { ChatMessage, SavedConversation } from '@/lib/types';
import { CONVERSATIONS_KEY } from '@/lib/constants';

export const useConversations = (currentChatHistory: ChatMessage[]) => {
    const [savedConversations, setSavedConversations] = useState<SavedConversation[]>([]);

    // Carica le conversazioni da localStorage all'avvio
    useEffect(() => {
        if (typeof window === 'undefined') return;

        const stored = localStorage.getItem(CONVERSATIONS_KEY);
        if (stored) {
            try {
                const parsed = JSON.parse(stored);
                setSavedConversations(parsed);
            } catch (e) {
                console.error("Errore nel parsing delle conversazioni salvate:", e);
                setSavedConversations([]);
            }
        }
    }, []);

    // Salva una conversazione
    const saveConversation = useCallback((name: string) => {
        if (typeof window === 'undefined') return false;
        if (currentChatHistory.length === 0) return false;

        const newConversation: SavedConversation = {
            id: Date.now().toString(),
            name: name,
            timestamp: new Date().toLocaleString('it-IT'),
            history: currentChatHistory,
        };

        const updated = [newConversation, ...savedConversations];
        localStorage.setItem(CONVERSATIONS_KEY, JSON.stringify(updated));
        setSavedConversations(updated);
        return true;
    }, [currentChatHistory, savedConversations]);

    // Elimina una conversazione
    const deleteConversation = useCallback((id: string) => {
        if (typeof window === 'undefined') return false;

        const updated = savedConversations.filter(conv => conv.id !== id);
        localStorage.setItem(CONVERSATIONS_KEY, JSON.stringify(updated));
        setSavedConversations(updated);
        return true;
    }, [savedConversations]);

    return { savedConversations, saveConversation, deleteConversation };
};
