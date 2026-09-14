"""Regression coverage for shared LLM capacity and provider deadlines."""

import asyncio
from threading import Event
from unittest.mock import Mock

import pytest
from fastapi import HTTPException

from app.routers import query_router
from app.schemas.rag_schema import SummarizeRequest
from app.services.query_concurrency_limiter import (
    GlobalExpensiveOperationLimiter,
    QueryConcurrencyLimiter,
)
from app.services.query_quota_service import QueryQuotaReservation


def _quota_service() -> Mock:
    quota = Mock()
    quota.reserve.return_value = QueryQuotaReservation("FREE", 20, 1)
    return quota


@pytest.mark.asyncio
async def test_summary_cannot_bypass_the_shared_global_limiter(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    global_limiter = GlobalExpensiveOperationLimiter(1)
    await global_limiter.acquire()
    monkeypatch.setattr(query_router, "global_expensive_operation_limiter", global_limiter)
    monkeypatch.setattr(query_router, "query_concurrency_limiter", QueryConcurrencyLimiter())
    rag = Mock()

    with pytest.raises(HTTPException) as error:
        await query_router.summarize_conversation(
            SummarizeRequest(conversation_history=[]), "other-user", rag, _quota_service()
        )

    assert error.value.status_code == 429
    rag.generate_conversation_summary.assert_not_called()
    await global_limiter.release()


@pytest.mark.asyncio
async def test_summary_releases_shared_capacity_after_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    global_limiter = GlobalExpensiveOperationLimiter(1)
    monkeypatch.setattr(query_router, "global_expensive_operation_limiter", global_limiter)
    monkeypatch.setattr(query_router, "query_concurrency_limiter", QueryConcurrencyLimiter())
    rag = Mock()
    rag.generate_conversation_summary.return_value = "summary"

    response = await query_router.summarize_conversation(
        SummarizeRequest(conversation_history=[]), "first-user", rag, _quota_service()
    )

    assert response.summary == "summary"
    assert global_limiter.active == 0
    assert await global_limiter.acquire() is True


@pytest.mark.asyncio
async def test_provider_error_is_redacted_and_releases_shared_capacity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    global_limiter = GlobalExpensiveOperationLimiter(1)
    monkeypatch.setattr(query_router, "global_expensive_operation_limiter", global_limiter)
    monkeypatch.setattr(query_router, "query_concurrency_limiter", QueryConcurrencyLimiter())
    rag = Mock()
    rag.generate_conversation_summary.side_effect = RuntimeError("provider secret detail")

    with pytest.raises(HTTPException) as error:
        await query_router.summarize_conversation(
            SummarizeRequest(conversation_history=[]), "user", rag, _quota_service()
        )

    assert error.value.status_code == 500
    assert error.value.detail == "Unable to generate the conversation summary. Please try again."
    assert "secret" not in error.value.detail
    assert global_limiter.active == 0
    assert await global_limiter.acquire() is True


@pytest.mark.asyncio
async def test_provider_timeout_returns_504_and_releases_capacity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    global_limiter = GlobalExpensiveOperationLimiter(1)
    started = Event()
    release_provider = Event()

    def stalled_provider(_history: object) -> str:
        started.set()
        release_provider.wait(timeout=1)
        return "late summary"

    monkeypatch.setattr(query_router, "LLM_TIMEOUT_SECONDS", 0.01)
    monkeypatch.setattr(query_router, "global_expensive_operation_limiter", global_limiter)
    monkeypatch.setattr(query_router, "query_concurrency_limiter", QueryConcurrencyLimiter())
    rag = Mock()
    rag.generate_conversation_summary.side_effect = stalled_provider

    with pytest.raises(HTTPException) as error:
        await query_router.summarize_conversation(
            SummarizeRequest(conversation_history=[]), "user", rag, _quota_service()
        )
    release_provider.set()

    assert started.is_set()
    assert error.value.status_code == 504
    assert error.value.detail == "The language service timed out. Please try again."
    assert global_limiter.active == 0

    normal_rag = Mock()
    normal_rag.generate_conversation_summary.return_value = "normal summary"
    response = await query_router.summarize_conversation(
        SummarizeRequest(conversation_history=[]), "other-user", normal_rag, _quota_service()
    )
    assert response.summary == "normal summary"


@pytest.mark.asyncio
async def test_cancelling_summary_releases_shared_capacity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    global_limiter = GlobalExpensiveOperationLimiter(1)
    started = Event()
    release_provider = Event()

    def stalled_provider(_history: object) -> str:
        started.set()
        release_provider.wait(timeout=1)
        return "late summary"

    monkeypatch.setattr(query_router, "global_expensive_operation_limiter", global_limiter)
    monkeypatch.setattr(query_router, "query_concurrency_limiter", QueryConcurrencyLimiter())
    rag = Mock()
    rag.generate_conversation_summary.side_effect = stalled_provider
    task = asyncio.create_task(
        query_router.summarize_conversation(
            SummarizeRequest(conversation_history=[]), "user", rag, _quota_service()
        )
    )
    assert await asyncio.to_thread(started.wait, 1)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    release_provider.set()

    assert global_limiter.active == 0
    assert await global_limiter.acquire() is True
