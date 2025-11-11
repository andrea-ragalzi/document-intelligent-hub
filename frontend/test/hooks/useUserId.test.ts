import { renderHook, waitFor } from '@testing-library/react'
import { describe, it, expect, beforeEach } from 'vitest'
import { useUserId } from '../../hooks/useUserId'

describe('useUserId', () => {
    beforeEach(() => {
        localStorage.clear()
    })

    it('should eventually generate a new user ID if none exists', async () => {
        const { result } = renderHook(() => useUserId())

        await waitFor(() => {
            expect(result.current.userId).toBeDefined()
            expect(result.current.isAuthReady).toBe(true)
        })

        expect(typeof result.current.userId).toBe('string')
        expect(result.current.userId).toMatch(/^user_/)
    })

    it('should persist user ID in localStorage', async () => {
        const { result } = renderHook(() => useUserId())

        await waitFor(() => {
            expect(result.current.userId).not.toBeNull()
        })

        const userId = result.current.userId
        expect(localStorage.getItem('ragUserId')).toBe(userId)
    })

    it('should return existing user ID from localStorage', async () => {
        const existingId = 'user_existing123'
        localStorage.setItem('ragUserId', existingId)

        const { result } = renderHook(() => useUserId())

        await waitFor(() => {
            expect(result.current.userId).toBe(existingId)
            expect(result.current.isAuthReady).toBe(true)
        })
    })

    it('should generate user_ prefixed format', async () => {
        const { result } = renderHook(() => useUserId())

        await waitFor(() => {
            expect(result.current.userId).not.toBeNull()
        })

        expect(result.current.userId).toMatch(/^user_[a-z0-9]+$/)
    })

    it('should use same ID across multiple hook instances', async () => {
        const { result: result1 } = renderHook(() => useUserId())

        await waitFor(() => {
            expect(result1.current.userId).not.toBeNull()
        })

        const { result: result2 } = renderHook(() => useUserId())

        await waitFor(() => {
            expect(result2.current.userId).toBe(result1.current.userId)
        })
    })

    it('should set isAuthReady to true after initialization', async () => {
        const { result } = renderHook(() => useUserId())

        await waitFor(() => {
            expect(result.current.isAuthReady).toBe(true)
        })
    })
})