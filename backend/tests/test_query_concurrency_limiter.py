"""Tests for the in-process per-user RAG concurrency guard."""

import asyncio

import pytest

from app.services.query_concurrency_limiter import GlobalExpensiveOperationLimiter, QueryConcurrencyLimiter


@pytest.mark.asyncio
async def test_same_user_cannot_acquire_two_rag_slots() -> None:
    """A second concurrent RAG request for the same UID is rejected."""
    limiter = QueryConcurrencyLimiter(max_concurrent_per_user=1)

    assert await limiter.acquire("user-a") is True
    await limiter.release("user-a")
    assert await limiter.acquire("user-a") is True
    assert await limiter.acquire("user-a") is False
    assert await limiter.acquire("user-b") is True


@pytest.mark.asyncio
async def test_releasing_slot_allows_later_request() -> None:
    """A completed or failed request must not leave the user blocked."""
    limiter = QueryConcurrencyLimiter(max_concurrent_per_user=1)

    assert await limiter.acquire("user-a") is True


@pytest.mark.asyncio
async def test_global_limiter_releases_after_success_failure_and_cancellation() -> None:
    limiter = GlobalExpensiveOperationLimiter(1)
    assert await limiter.acquire() is True
    await limiter.release()
    assert await limiter.acquire() is True
    try:
        raise RuntimeError("synthetic failure")
    except RuntimeError:
        await limiter.release()
    assert await limiter.acquire() is True
    try:
        raise asyncio.CancelledError()
    except asyncio.CancelledError:
        await limiter.release()
    assert await limiter.acquire() is True
