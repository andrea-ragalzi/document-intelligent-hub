"""Focused tests for private, idempotent starter-document seeding."""

from unittest.mock import AsyncMock, Mock

import pytest

from app.services.demo_document_service import (
    DEMO_DOCUMENT_FILENAME,
    DemoDocumentService,
)
from app.repositories.vector_store_repository import VectorStoreRepository
from app.services.rag_orchestrator_service import RAGService


@pytest.mark.asyncio
@pytest.mark.parametrize("user_id", ["free-user", "unlimited-user"])
async def test_all_tiers_get_the_same_private_demo_document(user_id: str) -> None:
    """Tier is deliberately irrelevant: every authenticated user receives a private seed."""
    rag_service = Mock(spec=RAGService)
    rag_service.user_document_exists.return_value = False
    rag_service.index_document = AsyncMock(return_value=(4, "EN"))

    result = await DemoDocumentService(rag_service).seed_for_user(user_id)

    assert result.status == "seeded"
    assert result.chunks_indexed == 4
    rag_service.user_document_exists.assert_called_once_with(
        user_id, DEMO_DOCUMENT_FILENAME
    )
    call = rag_service.index_document.await_args.kwargs
    assert call["user_id"] == user_id
    assert call["file"].filename == DEMO_DOCUMENT_FILENAME
    assert call["document_metadata"] == {"is_demo_document": True}


@pytest.mark.asyncio
async def test_repeated_seed_does_not_duplicate_the_demo_document() -> None:
    """A refresh or re-login finds the user's existing private Chroma chunks."""
    rag_service = Mock(spec=RAGService)
    rag_service.user_document_exists.side_effect = [False, True]
    rag_service.index_document = AsyncMock(return_value=(4, "EN"))
    service = DemoDocumentService(rag_service)

    first = await service.seed_for_user("user-a")
    second = await service.seed_for_user("user-a")

    assert first.status == "seeded"
    assert second.status == "ready"
    rag_service.index_document.assert_awaited_once()


@pytest.mark.asyncio
async def test_user_a_cannot_retrieve_user_bs_demo_document() -> None:
    """The normal seed metadata and retrieval filter remain scoped to one UID."""
    rag_service = Mock(spec=RAGService)
    rag_service.user_document_exists.return_value = False
    rag_service.index_document = AsyncMock(return_value=(4, "EN"))
    service = DemoDocumentService(rag_service)

    await service.seed_for_user("user-a")
    await service.seed_for_user("user-b")

    owners = [call.kwargs["user_id"] for call in rag_service.index_document.await_args_list]
    assert owners == ["user-a", "user-b"]

    vector_store = Mock()
    vector_store.similarity_search.return_value = []
    repository = VectorStoreRepository(vector_store=vector_store, collection=Mock())
    repository.similarity_search("Where did the Cat vanish?", user_id="user-a")

    vector_store.similarity_search.assert_called_once_with(
        query="Where did the Cat vanish?", k=10, filter={"source": "user-a"}
    )
