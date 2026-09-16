"""Focused tests for private, idempotent starter-document seeding."""

from unittest.mock import AsyncMock, Mock

import pytest

from app.services.demo_document_service import (
    DEMO_DOCUMENT_FILENAME,
    DEMO_DOCUMENT_PATH,
    DemoDocumentService,
)
from app.services.document_file_storage import DocumentFileStorage
from app.repositories.vector_store_repository import VectorStoreRepository
from app.services.rag_orchestrator_service import RAGService

LEGACY_DEMO_DOCUMENT_FILENAME = "alice-cheshire-cat-demo.pdf"


def test_full_alice_pdf_is_the_bundled_demo_document() -> None:
    """The demo fixture must be the complete Alice in Wonderland PDF."""
    assert DEMO_DOCUMENT_FILENAME == "alices-adventures-in-wonderland.pdf"
    assert DEMO_DOCUMENT_PATH.name == DEMO_DOCUMENT_FILENAME
    assert DEMO_DOCUMENT_PATH.read_bytes().startswith(b"%PDF")
    assert DEMO_DOCUMENT_PATH.stat().st_size > 1_000_000


@pytest.mark.asyncio
@pytest.mark.parametrize("user_id", ["free-user", "unlimited-user"])
async def test_all_tiers_get_the_same_private_demo_document(
    user_id: str, tmp_path
) -> None:
    """Tier is deliberately irrelevant: every authenticated user receives a private seed."""
    rag_service = Mock(spec=RAGService)
    rag_service.user_document_exists.return_value = False
    rag_service.index_document = AsyncMock(return_value=(4, "EN"))

    storage = DocumentFileStorage(tmp_path)
    result = await DemoDocumentService(rag_service, storage).seed_for_user(user_id)

    assert result.status == "seeded"
    assert result.chunks_indexed == 4
    rag_service.user_document_exists.assert_any_call(user_id, DEMO_DOCUMENT_FILENAME)
    call = rag_service.index_document.await_args.kwargs
    assert call["user_id"] == user_id
    assert call["file"].filename == DEMO_DOCUMENT_FILENAME
    assert call["file"].content == DEMO_DOCUMENT_PATH.read_bytes()
    assert call["document_metadata"] == {"is_demo_document": True}
    assert storage.get(user_id, DEMO_DOCUMENT_FILENAME) is not None


@pytest.mark.asyncio
async def test_repeated_seed_does_not_duplicate_the_demo_document(tmp_path) -> None:
    """A refresh or re-login finds the user's existing private Chroma chunks."""
    rag_service = Mock(spec=RAGService)
    rag_service.user_document_exists.side_effect = [False, False, True]
    rag_service.index_document = AsyncMock(return_value=(4, "EN"))
    service = DemoDocumentService(rag_service, DocumentFileStorage(tmp_path))

    first = await service.seed_for_user("user-a")
    second = await service.seed_for_user("user-a")

    assert first.status == "seeded"
    assert second.status == "ready"
    rag_service.index_document.assert_awaited_once()


@pytest.mark.asyncio
async def test_seed_replaces_the_legacy_alice_demo_document(tmp_path) -> None:
    """Existing excerpt seeds are removed before the complete Alice PDF is added."""
    rag_service = Mock(spec=RAGService)
    rag_service.user_document_exists.side_effect = lambda _user_id, filename: (
        filename == LEGACY_DEMO_DOCUMENT_FILENAME
    )
    rag_service.index_document = AsyncMock(return_value=(4, "EN"))
    storage = DocumentFileStorage(tmp_path)
    storage.store("user-a", LEGACY_DEMO_DOCUMENT_FILENAME, b"old excerpt")

    result = await DemoDocumentService(rag_service, storage).seed_for_user("user-a")

    assert result.status == "seeded"
    rag_service.delete_user_document.assert_called_once_with(
        "user-a", LEGACY_DEMO_DOCUMENT_FILENAME
    )
    assert storage.get("user-a", LEGACY_DEMO_DOCUMENT_FILENAME) is None
    assert storage.get("user-a", DEMO_DOCUMENT_FILENAME) is not None


@pytest.mark.asyncio
async def test_existing_demo_document_backfills_its_private_original(tmp_path) -> None:
    """Previously indexed demo chunks gain preview/download support on the next seed."""
    rag_service = Mock(spec=RAGService)
    rag_service.user_document_exists.return_value = True
    rag_service.index_document = AsyncMock()
    storage = DocumentFileStorage(tmp_path)

    result = await DemoDocumentService(rag_service, storage).seed_for_user("user-a")

    assert result.status == "ready"
    assert result.chunks_indexed == 0
    assert storage.get("user-a", DEMO_DOCUMENT_FILENAME) is not None
    rag_service.index_document.assert_not_awaited()


@pytest.mark.asyncio
async def test_failed_demo_original_storage_removes_indexed_chunks(tmp_path) -> None:
    """A storage failure after indexing cannot leave demo vectors behind."""
    rag_service = Mock(spec=RAGService)
    rag_service.user_document_exists.return_value = False
    rag_service.index_document = AsyncMock(return_value=(4, "EN"))
    storage = Mock(spec=DocumentFileStorage)
    storage.store.side_effect = OSError("disk full")
    service = DemoDocumentService(rag_service, storage)

    with pytest.raises(OSError, match="disk full"):
        await service.seed_for_user("user-a")

    rag_service.delete_user_document.assert_called_once_with(
        "user-a", DEMO_DOCUMENT_FILENAME
    )
    storage.delete.assert_called_once_with("user-a", DEMO_DOCUMENT_FILENAME)


@pytest.mark.asyncio
async def test_user_a_cannot_retrieve_user_bs_demo_document(tmp_path) -> None:
    """The normal seed metadata and retrieval filter remain scoped to one UID."""
    rag_service = Mock(spec=RAGService)
    rag_service.user_document_exists.return_value = False
    rag_service.index_document = AsyncMock(return_value=(4, "EN"))
    service = DemoDocumentService(rag_service, DocumentFileStorage(tmp_path))

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
