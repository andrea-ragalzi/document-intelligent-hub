/**
 * Tests for useQueryUsage Hook
 * 
 * Tests the hook that manages user query usage and limit checking.
 * Critical: UNLIMITED tier with remaining: -1 should NOT be considered limit reached.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useQueryUsage } from '@/hooks/useQueryUsage';
import * as AuthContext from '@/contexts/AuthContext';
import React from 'react';

// Mock AuthContext
vi.mock('@/contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}));

describe('useQueryUsage', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
        },
      },
    });
    vi.clearAllMocks();
  });

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );

  it('should return default values when user is not authenticated', async () => {
    vi.mocked(AuthContext.useAuth).mockReturnValue({
      user: null,
      loading: false,
    } as any);

    const { result } = renderHook(() => useQueryUsage(), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.queriesUsed).toBe(0);
    expect(result.current.queryLimit).toBe(0);
    expect(result.current.remaining).toBe(0);
    expect(result.current.tier).toBe('FREE');
    expect(result.current.isLimitReached).toBe(false);
  });

  it('should handle FREE tier with usage under limit', async () => {
    const mockUser = {
      uid: 'test_user',
      getIdToken: vi.fn().mockResolvedValue('mock_token'),
    };

    vi.mocked(AuthContext.useAuth).mockReturnValue({
      user: mockUser,
      loading: false,
    } as any);

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        status: 'success',
        queries_today: 10,
        query_limit: 20,
        remaining: 10,
        tier: 'FREE',
      }),
    });

    const { result } = renderHook(() => useQueryUsage(), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.queriesUsed).toBe(10);
    expect(result.current.queryLimit).toBe(20);
    expect(result.current.remaining).toBe(10);
    expect(result.current.tier).toBe('FREE');
    expect(result.current.isLimitReached).toBe(false);
  });

  it('should handle FREE tier at limit (remaining = 0)', async () => {
    const mockUser = {
      uid: 'test_user',
      getIdToken: vi.fn().mockResolvedValue('mock_token'),
    };

    vi.mocked(AuthContext.useAuth).mockReturnValue({
      user: mockUser,
      loading: false,
    } as any);

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        status: 'success',
        queries_today: 20,
        query_limit: 20,
        remaining: 0,
        tier: 'FREE',
      }),
    });

    const { result } = renderHook(() => useQueryUsage(), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.queriesUsed).toBe(20);
    expect(result.current.queryLimit).toBe(20);
    expect(result.current.remaining).toBe(0);
    expect(result.current.tier).toBe('FREE');
    expect(result.current.isLimitReached).toBe(true); // At limit
  });

  it('should handle UNLIMITED tier with remaining = -1', async () => {
    const mockUser = {
      uid: 'unlimited_user',
      getIdToken: vi.fn().mockResolvedValue('mock_token'),
    };

    vi.mocked(AuthContext.useAuth).mockReturnValue({
      user: mockUser,
      loading: false,
    } as any);

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        status: 'success',
        queries_today: 0,
        query_limit: 9999,
        remaining: -1, // UNLIMITED returns -1
        tier: 'UNLIMITED',
      }),
    });

    const { result } = renderHook(() => useQueryUsage(), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.queriesUsed).toBe(0);
    expect(result.current.queryLimit).toBe(9999);
    expect(result.current.remaining).toBe(-1);
    expect(result.current.tier).toBe('UNLIMITED');
    expect(result.current.isLimitReached).toBe(false); // CRITICAL: -1 should NOT be limit reached
  });

  it('should handle UNLIMITED tier with high usage (remaining = -1)', async () => {
    const mockUser = {
      uid: 'unlimited_user',
      getIdToken: vi.fn().mockResolvedValue('mock_token'),
    };

    vi.mocked(AuthContext.useAuth).mockReturnValue({
      user: mockUser,
      loading: false,
    } as any);

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        status: 'success',
        queries_today: 5000, // High usage
        query_limit: 9999,
        remaining: -1, // Still -1 for unlimited
        tier: 'UNLIMITED',
      }),
    });

    const { result } = renderHook(() => useQueryUsage(), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.queriesUsed).toBe(5000);
    expect(result.current.queryLimit).toBe(9999);
    expect(result.current.remaining).toBe(-1);
    expect(result.current.tier).toBe('UNLIMITED');
    expect(result.current.isLimitReached).toBe(false); // REGRESSION TEST: Bug was here!
  });

  it('should handle PRO tier with usage', async () => {
    const mockUser = {
      uid: 'pro_user',
      getIdToken: vi.fn().mockResolvedValue('mock_token'),
    };

    vi.mocked(AuthContext.useAuth).mockReturnValue({
      user: mockUser,
      loading: false,
    } as any);

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        status: 'success',
        queries_today: 150,
        query_limit: 500,
        remaining: 350,
        tier: 'PRO',
      }),
    });

    const { result } = renderHook(() => useQueryUsage(), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.queriesUsed).toBe(150);
    expect(result.current.queryLimit).toBe(500);
    expect(result.current.remaining).toBe(350);
    expect(result.current.tier).toBe('PRO');
    expect(result.current.isLimitReached).toBe(false);
  });

  it('should handle API error gracefully', async () => {
    const mockUser = {
      uid: 'test_user',
      getIdToken: vi.fn().mockResolvedValue('mock_token'),
    };

    vi.mocked(AuthContext.useAuth).mockReturnValue({
      user: mockUser,
      loading: false,
    } as any);

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
      json: async () => ({ detail: 'Server error' }),
    });

    const { result } = renderHook(() => useQueryUsage(), { wrapper });

    await waitFor(() => {
      expect(result.current.error).toBeTruthy();
    });

    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBeTruthy();
  });
});
