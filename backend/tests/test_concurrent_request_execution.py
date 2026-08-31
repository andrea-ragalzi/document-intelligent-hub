"""Focused checks that CPU-bound request work does not block FastAPI's event loop."""

import asyncio
import time
from io import BytesIO
from threading import Event
from typing import Any
from unittest.mock import Mock, patch

import pytest
from fastapi import HTTPException, UploadFile
from langchain_core.documents import Document

from app.routers import query_router
from app.schemas.rag_schema import FileFilterResponse, QueryRequest
from app.services.document_classifier_service import DocumentCategory
from app.services.document_indexing_service import DocumentIndexingService
from app.services.query_concurrency_limiter import QueryConcurrencyLimiter


@pytest.mark.asyncio
async def test_two_pdf_indexes_progress_concurrently() -> None:
    """Two independent uploads must enter parsing without serializing the event loop."""
    repository = Mock()
    language_service = Mock()
    language_service.detect_language.return_value = "EN"
    classifier_service = Mock()
    classifier_service.classify_document.return_value = (
        DocumentCategory.INFORMATIVO_NON_STRUTTURATO
    )
    classifier_service.has_structural_density.return_value = False
    service = DocumentIndexingService(repository, language_service, classifier_service)
    loaded_documents = [
        Document(page_content="A sufficiently long document body for testing.", metadata={})
    ]

    loader = Mock()
    loader.load.side_effect = lambda: (time.sleep(0.15), loaded_documents)[1]
    first = UploadFile(file=BytesIO(b"%PDF-1.4 first"), filename="first.pdf")
    second = UploadFile(file=BytesIO(b"%PDF-1.4 second"), filename="second.pdf")

    with patch(
        "app.services.document_indexing_service.UnstructuredPDFLoader", return_value=loader
    ):
        start = time.monotonic()
        results = await asyncio.gather(
            service.index_document(first, "user-a"),
            service.index_document(second, "user-b"),
        )

    assert time.monotonic() - start < 0.28
    assert len(results) == 2
    indexed_batches = [call.args[0] for call in repository.add_documents.call_args_list]
    assert {batch[0].metadata["source"] for batch in indexed_batches} == {
        "user-a",
        "user-b",
    }


@pytest.mark.asyncio
async def test_independent_rag_queries_progress_concurrently(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Blocking retrieval/LLM work must run in worker threads per request."""

    class UsageService:
        def reserve_query_slot(self, _user_id: str, _max_queries: int) -> tuple[bool, int]:
            return True, 1

    class RAGService:
        def get_user_documents(self, _user_id: str) -> list[Any]:
            return []

        def answer_query(self, _query: str, user_id: str, *_args: Any, **_kwargs: Any) -> tuple[str, list[str]]:
            time.sleep(0.15)
            return f"answer for {user_id}", [f"{user_id}.pdf"]

    parser_result = FileFilterResponse(
        include_files=[], exclude_files=[], original_query="question", cleaned_query="question"
    )
    monkeypatch.setattr(query_router, "_get_user_tier_limits", lambda _uid: ("FREE", 20))
    monkeypatch.setattr(query_router, "_reserve_and_enforce_query_limit", lambda *_args: 1)
    monkeypatch.setattr(query_router, "get_usage_service", lambda: UsageService())
    monkeypatch.setattr(
        query_router.query_parser_service, "extract_file_filters", lambda **_kwargs: parser_result
    )

    request = QueryRequest(query="question", conversation_history=[])
    start = time.monotonic()
    responses = await asyncio.gather(
        query_router.query_document(request, "user-a", RAGService()),
        query_router.query_document(request, "user-b", RAGService()),
    )

    assert time.monotonic() - start < 0.28
    assert [response.source_documents for response in responses] == [
        ["user-a.pdf"],
        ["user-b.pdf"],
    ]


@pytest.mark.asyncio
async def test_second_same_user_query_is_rejected_while_first_is_running(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Double-clicks cannot start two expensive RAG requests for one UID."""
    started = Event()
    release = Event()

    class UsageService:
        def reserve_query_slot(self, _user_id: str, _max_queries: int) -> tuple[bool, int]:
            return True, 1

    class RAGService:
        def get_user_documents(self, _user_id: str) -> list[Any]:
            return []

        def answer_query(self, *_args: Any, **_kwargs: Any) -> tuple[str, list[str]]:
            started.set()
            assert release.wait(timeout=1)
            return "answer", ["user-a.pdf"]

    parser_result = FileFilterResponse(
        include_files=[], exclude_files=[], original_query="question", cleaned_query="question"
    )
    monkeypatch.setattr(query_router, "_get_user_tier_limits", lambda _uid: ("FREE", 20))
    monkeypatch.setattr(query_router, "get_usage_service", lambda: UsageService())
    monkeypatch.setattr(
        query_router,
        "query_concurrency_limiter",
        QueryConcurrencyLimiter(max_concurrent_per_user=1),
    )
    monkeypatch.setattr(
        query_router.query_parser_service, "extract_file_filters", lambda **_kwargs: parser_result
    )

    request = QueryRequest(query="question", conversation_history=[])
    first_query = asyncio.create_task(
        query_router.query_document(request, "user-a", RAGService())
    )
    assert await asyncio.to_thread(started.wait, 1)

    with pytest.raises(HTTPException, match="already running") as error:
        await query_router.query_document(request, "user-a", RAGService())

    assert getattr(error.value, "status_code", None) == 429
    release.set()
    await first_query
