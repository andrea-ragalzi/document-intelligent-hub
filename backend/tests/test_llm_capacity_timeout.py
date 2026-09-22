"""Regression coverage for shared LLM capacity and provider deadlines."""

import asyncio
from threading import Event
from unittest.mock import Mock

import pytest
from fastapi import HTTPException
from openai import APITimeoutError

from app.core.auth import WorkspaceAccess
from app.routers import query_router
from app.schemas.rag_schema import FileFilterResponse, QueryRequest, SummarizeRequest
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
async def test_query_and_summary_share_global_capacity_across_users(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    global_limiter = GlobalExpensiveOperationLimiter(1)
    query_started = Event()
    release_query = Event()

    class RAG:
        def get_user_documents(self, _user_id: str) -> list[object]:
            return []

        def answer_query(self, *_args: object, **_kwargs: object) -> tuple[str, list[str]]:
            query_started.set()
            release_query.wait(timeout=1)
            return "answer", []

        def generate_conversation_summary(self, _history: object) -> str:
            return "summary"

    parser_result = FileFilterResponse(
        include_files=[], exclude_files=[], original_query="query", cleaned_query="query"
    )
    monkeypatch.setattr(query_router, "global_expensive_operation_limiter", global_limiter)
    monkeypatch.setattr(query_router, "query_concurrency_limiter", QueryConcurrencyLimiter())
    monkeypatch.setattr(
        query_router.query_parser_service,
        "extract_file_filters",
        lambda **_kwargs: parser_result,
    )
    rag = RAG()
    query_task = asyncio.create_task(
        query_router.query_document(
            QueryRequest(query="query"),
            Mock(),
            WorkspaceAccess("query-user", "query-user", False),
            rag,
            _quota_service(),
            Mock(),
        )
    )
    assert await asyncio.to_thread(query_started.wait, 1)

    with pytest.raises(HTTPException) as error:
        await query_router.summarize_conversation(
            SummarizeRequest(conversation_history=[]), "summary-user", rag, _quota_service()
        )

    assert error.value.status_code == 429
    release_query.set()
    await query_task
    await _wait_for_release(global_limiter)


@pytest.mark.asyncio
async def test_global_capacity_allows_configured_summaries_then_rejects_another_user(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    global_limiter = GlobalExpensiveOperationLimiter(2)
    started = 0
    both_started = Event()
    release_provider = Event()

    def stalled_provider(_history: object) -> str:
        nonlocal started
        started += 1
        if started == 2:
            both_started.set()
        release_provider.wait(timeout=1)
        return "summary"

    monkeypatch.setattr(query_router, "global_expensive_operation_limiter", global_limiter)
    monkeypatch.setattr(query_router, "query_concurrency_limiter", QueryConcurrencyLimiter())
    first_rag = Mock()
    second_rag = Mock()
    first_rag.generate_conversation_summary.side_effect = stalled_provider
    second_rag.generate_conversation_summary.side_effect = stalled_provider
    first = asyncio.create_task(
        query_router.summarize_conversation(
            SummarizeRequest(conversation_history=[]), "first-user", first_rag, _quota_service()
        )
    )
    second = asyncio.create_task(
        query_router.summarize_conversation(
            SummarizeRequest(conversation_history=[]), "second-user", second_rag, _quota_service()
        )
    )
    assert await asyncio.to_thread(both_started.wait, 1)

    with pytest.raises(HTTPException) as error:
        await query_router.summarize_conversation(
            SummarizeRequest(conversation_history=[]), "third-user", Mock(), _quota_service()
        )
    assert error.value.status_code == 429

    release_provider.set()
    await asyncio.gather(first, second)
    await _wait_for_release(global_limiter)


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
async def test_provider_transport_timeout_returns_redacted_504(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    global_limiter = GlobalExpensiveOperationLimiter(1)
    monkeypatch.setattr(query_router, "global_expensive_operation_limiter", global_limiter)
    monkeypatch.setattr(query_router, "query_concurrency_limiter", QueryConcurrencyLimiter())
    rag = Mock()
    rag.generate_conversation_summary.side_effect = APITimeoutError(request=Mock())

    with pytest.raises(HTTPException) as error:
        await query_router.summarize_conversation(
            SummarizeRequest(conversation_history=[]), "user", rag, _quota_service()
        )

    assert error.value.status_code == 504
    assert error.value.detail == "The language service timed out. Please try again."
    assert global_limiter.active == 0


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

    monkeypatch.setattr(query_router.settings, "OPENAI_TIMEOUT_SECONDS", 0.01)
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
    await _wait_for_release(global_limiter)
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

    await _wait_for_release(global_limiter)
    assert global_limiter.active == 0
    assert await global_limiter.acquire() is True


async def _wait_for_release(limiter: GlobalExpensiveOperationLimiter) -> None:
    """Wait only for a fake provider thread to finish after it has been released."""
    async with asyncio.timeout(1):
        while limiter.active:
            await asyncio.sleep(0)
