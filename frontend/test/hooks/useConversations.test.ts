import { renderHook, act, waitFor } from '@testing-library/react'
import { describe, it, expect, beforeEach } from 'vitest'
import { useConversations } from '../../hooks/useConversations'
import type { ChatMessage } from '../../lib/types'

describe('useConversations', () => {
    const mockChatHistory: ChatMessage[] = [
        { type: 'user', text: 'Hello AI', sources: [] },
        { type: 'assistant', text: 'Hello! How can I help?', sources: [] },
    ]

    beforeEach(() => {
        localStorage.clear()
    })

    it('should initialize with empty conversations array', () => {
        const { result } = renderHook(() => useConversations([]))

        expect(result.current.savedConversations).toEqual([])
    })

    it('should load saved conversations from localStorage', async () => {
        const mockSaved = [
            {
                id: '123',
                name: 'Test Conversation',
                timestamp: '2025-01-01',
                history: mockChatHistory,
            },
        ]

        localStorage.setItem('rag_conversations', JSON.stringify(mockSaved))

        const { result } = renderHook(() => useConversations([]))

        await waitFor(() => {
            expect(result.current.savedConversations).toEqual(mockSaved)
        })
    })

    it('should save a new conversation', async () => {
        const { result } = renderHook(() => useConversations(mockChatHistory))

        let saved = false
        await act(async () => {
            saved = result.current.saveConversation('My First Chat')
        })

        expect(saved).toBe(true)
        expect(result.current.savedConversations).toHaveLength(1)
        expect(result.current.savedConversations[0].name).toBe('My First Chat')
        expect(result.current.savedConversations[0].history).toEqual(mockChatHistory)
    })

    it('should not save conversation with empty chat history', async () => {
        const { result } = renderHook(() => useConversations([]))

        let saved = false
        await act(async () => {
            saved = result.current.saveConversation('Empty Chat')
        })

        expect(saved).toBe(false)
        expect(result.current.savedConversations).toHaveLength(0)
    })

    it('should persist conversations in localStorage', async () => {
        const { result } = renderHook(() => useConversations(mockChatHistory))

        await act(async () => {
            result.current.saveConversation('Persisted Chat')
        })

        const stored = localStorage.getItem('rag_conversations')
        expect(stored).toBeDefined()

        const parsed = JSON.parse(stored!)
        expect(parsed).toHaveLength(1)
        expect(parsed[0].name).toBe('Persisted Chat')
    })

    it('should delete a conversation by id', async () => {
        // Pre-populate localStorage with two conversations
        const preExisting = [
            {
                id: 'conv-1',
                name: 'Chat 1',
                timestamp: '2025-01-01',
                history: mockChatHistory,
            },
            {
                id: 'conv-2',
                name: 'Chat 2',
                timestamp: '2025-01-02',
                history: mockChatHistory,
            },
        ]
        localStorage.setItem('rag_conversations', JSON.stringify(preExisting))

        const { result } = renderHook(() => useConversations([]))

        await waitFor(() => {
            expect(result.current.savedConversations).toHaveLength(2)
        })

        // Delete first conversation (conv-2)
        let deleted = false
        await act(async () => {
            deleted = result.current.deleteConversation('conv-1')
        })

        expect(deleted).toBe(true)
        expect(result.current.savedConversations).toHaveLength(1)
        expect(result.current.savedConversations[0].name).toBe('Chat 2')
    })

    it('should handle corrupted localStorage data gracefully', async () => {
        localStorage.setItem('rag_conversations', 'invalid json')

        const { result } = renderHook(() => useConversations([]))

        await waitFor(() => {
            expect(result.current.savedConversations).toEqual([])
        })
    })

    it('should generate unique IDs for conversations', async () => {
        const { result } = renderHook(() => useConversations(mockChatHistory))

        await act(async () => {
            result.current.saveConversation('Chat 1')
        })

        expect(result.current.savedConversations).toHaveLength(1)
        const firstId = result.current.savedConversations[0].id

        // Mount a new hook instance
        const { result: result2 } = renderHook(() => useConversations(mockChatHistory))

        await act(async () => {
            result2.current.saveConversation('Chat 2')
        })

        expect(result2.current.savedConversations).toHaveLength(2)
        const secondId = result2.current.savedConversations[0].id

        // IDs should be different
        expect(firstId).not.toBe(secondId)
    })

    it('should prepend new conversations to the beginning', async () => {
        const { result } = renderHook(() => useConversations(mockChatHistory))

        await act(async () => {
            result.current.saveConversation('First')
        })

        await act(async () => {
            result.current.saveConversation('Second')
        })

        // Most recent should be first
        expect(result.current.savedConversations[0].name).toBe('Second')
        expect(result.current.savedConversations[1].name).toBe('First')
    })
})
