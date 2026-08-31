"""Regression tests for admission control before expensive DIH work."""

import asyncio
from io import BytesIO
from threading import Event
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import HTTPException, UploadFile
from langchain_core.documents import Document

from app.core.auth import require_verified_email
from app.config.security_constants import UNLIMITED_TIER_MAX_QUERIES
from app.core.constants import ConversationConstants, LLMConstants, QueryConstants
from app.routers import documents_router, query_router
from app.schemas.rag_schema import ConversationMessage, QueryRequest, SummarizeRequest
from app.services.conversation_service import ConversationService
from app.services.document_classifier_service import DocumentCategory
from app.services.document_indexing_service import DocumentIndexingService
from app.services.query_concurrency_limiter import QueryConcurrencyLimiter
from main import app


def test_query_rejects_oversized_input_before_router_work() -> None:
    with pytest.raises(ValueError):
        QueryRequest(query="x" * (QueryConstants.MAX_QUERY_LENGTH + 1))


def test_oversized_query_endpoint_never_reaches_openai_backed_parser(client: object) -> None:
    parser = Mock()
    with patch.object(query_router.query_parser_service, "extract_file_filters", parser):
        response = client.post(  # type: ignore[attr-defined]
            "/rag/query/", json={"query": "x" * (QueryConstants.MAX_QUERY_LENGTH + 1)}
        )
    assert response.status_code == 422
    parser.assert_not_called()


def test_unverified_firebase_user_is_rejected_before_expensive_work() -> None:
    with patch("app.core.auth.auth.get_user") as get_user:
        get_user.return_value.email_verified = False
        with pytest.raises(HTTPException) as error:
            require_verified_email("verified-token-uid")
    assert error.value.status_code == 403


def test_summarize_without_authentication_is_rejected(client: object) -> None:
    client.test_user_context["user_id"] = None  # type: ignore[attr-defined]
    response = client.post("/rag/summarize/", json={"conversation_history": []})  # type: ignore[attr-defined]
    assert response.status_code == 401


def test_unverified_user_cannot_reach_query_parser(
    client: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    def reject_unverified() -> str:
        raise HTTPException(status_code=403, detail="Email verification required")

    parser = Mock()
    monkeypatch.setattr(query_router.query_parser_service, "extract_file_filters", parser)
    app.dependency_overrides[require_verified_email] = reject_unverified
    try:
        response = client.post("/rag/query/", json={"query": "valid question"})  # type: ignore[attr-defined]
    finally:
        app.dependency_overrides.pop(require_verified_email, None)

    assert response.status_code == 403
    parser.assert_not_called()


def test_query_rejects_too_many_history_messages_before_router_work() -> None:
    messages = [
        {"role": "user", "content": "ok"}
        for _ in range(ConversationConstants.MAX_HISTORY_MESSAGES + 1)
    ]
    with pytest.raises(ValueError):
        QueryRequest(query="valid question", conversation_history=messages)


def test_query_rejects_oversized_history_message_before_router_work() -> None:
    with pytest.raises(ValueError):
        QueryRequest(
            query="valid question",
            conversation_history=[
                {
                    "role": "user",
                    "content": "x" * (ConversationConstants.MAX_HISTORY_MESSAGE_LENGTH + 1),
                }
            ],
        )


def test_summarize_rejects_oversized_history_before_model_invocation() -> None:
    with pytest.raises(ValueError):
        SummarizeRequest(
            conversation_history=[
                {"role": "user", "content": "ok"}
                for _ in range(ConversationConstants.MAX_SUMMARY_HISTORY_MESSAGES + 1)
            ]
        )


def test_summary_uses_explicit_server_side_token_limit() -> None:
    llm = Mock()
    llm.invoke.return_value.content = "brief summary"

    summary = ConversationService(llm).generate_conversation_summary(
        [ConversationMessage(role="user", content="hello")]
    )

    assert summary == "brief summary"
    llm.invoke.assert_called_once()
    assert llm.invoke.call_args.kwargs["max_tokens"] == LLMConstants.MAX_SUMMARY_TOKENS


def test_unlimited_tier_has_a_finite_hard_cap() -> None:
    user = Mock()
    user.custom_claims = {"tier": "UNLIMITED"}
    with patch("app.routers.query_router.auth.get_user", return_value=user):
        tier, max_queries = query_router._get_user_tier_limits("any-user")
    assert tier == "UNLIMITED"
    assert max_queries == UNLIMITED_TIER_MAX_QUERIES
    assert max_queries < 9999


@pytest.mark.asyncio
async def test_summarize_rejects_exhausted_quota_before_model(monkeypatch: pytest.MonkeyPatch) -> None:
    class Usage:
        def reserve_query_slot(self, *_args: object) -> tuple[bool, int]:
            return False, 20

    rag = Mock()
    rag.generate_conversation_summary = Mock()
    monkeypatch.setattr(query_router, "_get_user_tier_limits", lambda _uid: ("FREE", 20))
    monkeypatch.setattr(query_router, "get_usage_service", lambda: Usage())
    monkeypatch.setattr(query_router, "query_concurrency_limiter", QueryConcurrencyLimiter())

    with pytest.raises(HTTPException, match="Daily query limit") as error:
        await query_router.summarize_conversation(
            SummarizeRequest(conversation_history=[]), "verified-user", rag
        )

    assert error.value.status_code == 429
    rag.generate_conversation_summary.assert_not_called()


@pytest.mark.asyncio
async def test_valid_summary_reserves_quota_before_invoking_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    class Usage:
        def reserve_query_slot(self, *_args: object) -> tuple[bool, int]:
            calls.append("reserved")
            return True, 1

    rag = Mock()
    rag.generate_conversation_summary = Mock(return_value="summary")
    monkeypatch.setattr(query_router, "_get_user_tier_limits", lambda _uid: ("FREE", 20))
    monkeypatch.setattr(query_router, "get_usage_service", lambda: Usage())
    monkeypatch.setattr(query_router, "query_concurrency_limiter", QueryConcurrencyLimiter())

    response = await query_router.summarize_conversation(
        SummarizeRequest(conversation_history=[]), "verified-user", rag
    )

    assert response.summary == "summary"
    assert calls == ["reserved"]
    rag.generate_conversation_summary.assert_called_once_with([])


@pytest.mark.asyncio
async def test_upload_guard_admits_only_one_same_user_upload(monkeypatch: pytest.MonkeyPatch) -> None:
    limiter = QueryConcurrencyLimiter()
    monkeypatch.setattr(documents_router, "upload_concurrency_limiter", limiter)
    assert await limiter.acquire("same-user") is True
    assert await limiter.acquire("same-user") is False
    await limiter.release("same-user")


@pytest.mark.asyncio
async def test_concurrent_upload_at_document_limit_does_not_start_second_index(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    started = Event()
    release = Event()

    class RAG:
        async def index_document(self, **_kwargs: object) -> tuple[int, str]:
            started.set()
            assert await asyncio.to_thread(release.wait, 1)
            return 1, "EN"

    monkeypatch.setattr(documents_router, "upload_concurrency_limiter", QueryConcurrencyLimiter())
    monkeypatch.setattr(documents_router, "_check_file_limits", lambda *_args: (1024, 1.0))
    first = asyncio.create_task(
        documents_router.upload_document(
            None,
            UploadFile(file=BytesIO(b"%PDF-one"), filename="one.pdf"),
            "same-user",
            RAG(),
        )
    )
    assert await asyncio.to_thread(started.wait, 1)
    with pytest.raises(HTTPException) as error:
        await documents_router.upload_document(
            None,
            UploadFile(file=BytesIO(b"%PDF-two"), filename="two.pdf"),
            "same-user",
            RAG(),
        )
    assert error.value.status_code == 429
    release.set()
    assert (await first).chunks_indexed == 1


@pytest.mark.asyncio
async def test_detect_language_rejects_oversized_file_before_parser(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rag = Mock()
    rag.detect_document_language_preview = AsyncMock()
    monkeypatch.setattr(documents_router, "get_max_upload_size_bytes", lambda _uid: 10)
    monkeypatch.setattr(
        documents_router, "language_preview_concurrency_limiter", QueryConcurrencyLimiter()
    )

    with pytest.raises(HTTPException) as error:
        await documents_router.detect_document_language(
            UploadFile(file=BytesIO(b"x" * 11), filename="oversized.pdf"),
            "verified-user",
            rag,
        )

    assert error.value.status_code == 413
    rag.detect_document_language_preview.assert_not_awaited()


@pytest.mark.asyncio
async def test_valid_detect_language_preview_still_works(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rag = Mock()
    rag.detect_document_language_preview = AsyncMock(return_value=("EN", 0.9))
    monkeypatch.setattr(documents_router, "get_max_upload_size_bytes", lambda _uid: 100)
    monkeypatch.setattr(
        documents_router, "language_preview_concurrency_limiter", QueryConcurrencyLimiter()
    )

    response = await documents_router.detect_document_language(
        UploadFile(file=BytesIO(b"%PDF-valid"), filename="valid.pdf"),
        "verified-user",
        rag,
    )

    assert response.detected_language == "EN"
    rag.detect_document_language_preview.assert_awaited_once()


@pytest.mark.asyncio
async def test_second_language_preview_for_same_user_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    started = Event()
    release = Event()

    class RAG:
        async def detect_document_language_preview(self, **_kwargs: object) -> tuple[str, float]:
            started.set()
            assert await asyncio.to_thread(release.wait, 1)
            return "EN", 0.9

    monkeypatch.setattr(documents_router, "get_max_upload_size_bytes", lambda _uid: 100)
    monkeypatch.setattr(
        documents_router, "language_preview_concurrency_limiter", QueryConcurrencyLimiter()
    )
    first = asyncio.create_task(
        documents_router.detect_document_language(
            UploadFile(file=BytesIO(b"%PDF-one"), filename="one.pdf"),
            "same-user",
            RAG(),
        )
    )
    assert await asyncio.to_thread(started.wait, 1)
    with pytest.raises(HTTPException) as error:
        await documents_router.detect_document_language(
            UploadFile(file=BytesIO(b"%PDF-two"), filename="two.pdf"),
            "same-user",
            RAG(),
        )
    assert error.value.status_code == 429
    release.set()
    await first


@pytest.mark.asyncio
async def test_indexing_rejects_excessive_text_before_embeddings(monkeypatch: pytest.MonkeyPatch) -> None:
    repository = Mock()
    language_service = Mock()
    classifier = Mock()
    classifier.classify_document.return_value = DocumentCategory.INFORMATIVO_NON_STRUTTURATO
    classifier.has_structural_density.return_value = False
    service = DocumentIndexingService(repository, language_service, classifier)
    documents = [Document(page_content="x" * 200, metadata={})]
    monkeypatch.setattr(
        "app.services.document_indexing_service.UnstructuredPDFLoader",
        lambda *_args, **_kwargs: Mock(load=lambda: documents),
    )
    monkeypatch.setattr("app.services.document_indexing_service.MAX_EXTRACTED_DOCUMENT_TEXT", 100)

    with pytest.raises(ValueError, match="too much extracted text"):
        await service.index_document(
            UploadFile(file=BytesIO(b"%PDF-test"), filename="large.pdf"), "user"
        )
    repository.add_documents.assert_not_called()


@pytest.mark.asyncio
async def test_indexing_rejects_excessive_chunks_before_embeddings(monkeypatch: pytest.MonkeyPatch) -> None:
    repository = Mock()
    language_service = Mock()
    classifier = Mock()
    classifier.classify_document.return_value = DocumentCategory.INFORMATIVO_NON_STRUTTURATO
    classifier.has_structural_density.return_value = False
    service = DocumentIndexingService(repository, language_service, classifier)
    documents = [Document(page_content="normal content", metadata={})]
    monkeypatch.setattr(
        "app.services.document_indexing_service.UnstructuredPDFLoader",
        lambda *_args, **_kwargs: Mock(load=lambda: documents),
    )
    monkeypatch.setattr(
        service, "_apply_chunking_strategy", lambda *_args: [Document(page_content="x", metadata={})] * 2
    )
    monkeypatch.setattr("app.services.document_indexing_service.MAX_DOCUMENT_CHUNKS", 1)

    with pytest.raises(ValueError, match="too many chunks"):
        await service.index_document(
            UploadFile(file=BytesIO(b"%PDF-test"), filename="many.pdf"), "user"
        )
    repository.add_documents.assert_not_called()
