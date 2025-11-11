'use client';

import { useState, useCallback } from 'react';
import type { FormEvent } from 'react';
import type { ChatMessage } from '@/lib/types';
import { API_BASE_URL } from '@/lib/constants';

interface UseChatResult {
    query: string;
    setQuery: React.Dispatch<React.SetStateAction<string>>;
    chatHistory: ChatMessage[];
    setChatHistory: React.Dispatch<React.SetStateAction<ChatMessage[]>>;
    isQuerying: boolean;
    handleQuerySubmit: (e: FormEvent, currentUserId: string) => Promise<void>;
}

export const useRAGChat = (): UseChatResult => {
    const [query, setQuery] = useState<string>('');
    const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
    const [isQuerying, setIsQuerying] = useState<boolean>(false);

    const handleQuerySubmit = useCallback(async (e: FormEvent, currentUserId: string) => {
        e.preventDefault();
        if (!query.trim() || !currentUserId || isQuerying) return;

        const userQuery = query.trim();
        setQuery('');

        setChatHistory(prev => [...prev,
        { type: 'user', text: userQuery, sources: [] },
        {
            type: 'assistant',
            text: "L'Assistente sta analizzando i documenti indicizzati e generando la risposta...",
            sources: [],
            isThinking: true
        }
        ]);

        setIsQuerying(true);

        try {
            const response = await fetch(`${API_BASE_URL}/query/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: userQuery, user_id: currentUserId }),
            });

            const data = await response.json();

            setChatHistory(prev => {
                const newMessages = [...prev];
                const lastIndex = newMessages.length - 1;

                if (newMessages[lastIndex].isThinking) {
                    if (response.ok) {
                        newMessages[lastIndex] = {
                            type: 'assistant',
                            text: data.answer,
                            sources: data.source_documents || [],
                        };
                    } else {
                        newMessages[lastIndex] = {
                            type: 'assistant',
                            text: `[ERRORE API] Impossibile ottenere la risposta: ${data.detail || response.statusText}. Controlla i log del backend.`,
                            sources: [],
                        };
                    }
                }
                return newMessages;
            });

        } catch (error) {
            console.error('Query Error:', error);

            setChatHistory(prev => {
                const newMessages = [...prev];
                const lastIndex = newMessages.length - 1;
                if (newMessages[lastIndex].isThinking) {
                    newMessages[lastIndex] = {
                        type: 'assistant',
                        text: `[ERRORE DI RETE] Impossibile connettersi al backend. Assicurati che l'API sia attiva.`,
                        sources: [],
                    };
                }
                return newMessages;
            });

        } finally {
            setIsQuerying(false);
        }
    }, [query, isQuerying]);

    return { query, setQuery, chatHistory, setChatHistory, isQuerying, handleQuerySubmit };
};
