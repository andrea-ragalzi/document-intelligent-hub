"""Persistence and serialization regressions for the Alice lifecycle."""

import asyncio
from unittest.mock import Mock, patch

import pytest
from app.schemas.rag_schema import DocumentInfo
from app.services.demo_document_service import (
    DEMO_DOCUMENT_FILENAME,
    DemoDocumentService,
)
from app.services.demo_document_state_service import DemoDocumentStateService
from app.services.document_file_storage import DocumentFileStorage
from app.routers import documents_router


def test_demo_state_reads_and_writes_persisted_flags() -> None:
    document_ref = Mock()
    snapshot = Mock(exists=True)
    snapshot.to_dict.return_value = {
        "demo_document_deleted": True,
    }
    document_ref.get.return_value = snapshot
    database = Mock()
    database.collection.return_value.document.return_value = document_ref

    with patch("app.services.demo_document_state_service.firestore.client", return_value=database):
        state = DemoDocumentStateService()
        assert state.is_deleted("user-a") is True
        state.mark_deleted("user-a")

    assert document_ref.set.call_args_list[0].args[0] == {"demo_document_deleted": True}


class _LifecycleState:
    def __init__(self) -> None:
        self.deleted = False

    def is_deleted(self, _user_id: str) -> bool:
        return self.deleted

    def mark_deleted(self, _user_id: str) -> None:
        self.deleted = True


@pytest.mark.asyncio
async def test_inflight_seed_cannot_recreate_alice_after_serialized_delete(tmp_path) -> None:
    """The shared user lock makes delete wait for the seed, then suppresses retries."""
    state = _LifecycleState()
    started_indexing = asyncio.Event()
    release_indexing = asyncio.Event()
    documents: list[DocumentInfo] = []

    class RAG:
        def get_user_documents(self, _user_id: str) -> list[DocumentInfo]:
            return documents

        def user_document_exists(self, _user_id: str, filename: str) -> bool:
            return any(document.filename == filename for document in documents)

        async def index_document(self, **_kwargs: object) -> tuple[int, str]:
            started_indexing.set()
            await release_indexing.wait()
            documents.append(
                DocumentInfo(
                    filename=DEMO_DOCUMENT_FILENAME,
                    chunks_count=1,
                    is_demo_document=True,
                )
            )
            return 1, "EN"

        def delete_user_document(
            self, _user_id: str | None = None, filename: str = "", **_kwargs: object
        ) -> int:
            before = len(documents)
            documents[:] = [document for document in documents if document.filename != filename]
            return before - len(documents)

    rag = RAG()
    storage = DocumentFileStorage(tmp_path)
    service = DemoDocumentService(rag, storage, state_service=state)  # type: ignore[arg-type]

    seed = asyncio.create_task(service.seed_for_user("user-a"))
    await started_indexing.wait()
    delete_entered = asyncio.Event()

    async def delete_after_seed() -> None:
        # This mirrors the router's deletion critical section without sleeps.
        from app.services.demo_document_service import get_demo_document_lock

        delete_entered.set()
        lock = await get_demo_document_lock("user-a")
        async with lock:
            state.mark_deleted("user-a")
            storage.delete("user-a", DEMO_DOCUMENT_FILENAME)
            rag.delete_user_document("user-a", DEMO_DOCUMENT_FILENAME)

    delete = asyncio.create_task(delete_after_seed())
    await delete_entered.wait()
    release_indexing.set()
    await seed
    await delete

    assert documents == []
    assert storage.get("user-a", DEMO_DOCUMENT_FILENAME) is None
    assert (await service.seed_for_user("user-a")).status == "absent"


@pytest.mark.asyncio
async def test_router_seed_and_delete_share_the_same_lock(tmp_path, monkeypatch) -> None:
    """The actual seed and delete router handlers serialize one user's lifecycle."""
    state = _LifecycleState()
    started_indexing = asyncio.Event()
    release_indexing = asyncio.Event()
    documents: list[DocumentInfo] = []

    class RAG:
        def get_user_documents(self, _user_id: str) -> list[DocumentInfo]:
            return documents

        def user_document_exists(self, _user_id: str, filename: str) -> bool:
            return any(document.filename == filename for document in documents)

        async def index_document(self, **_kwargs: object) -> tuple[int, str]:
            started_indexing.set()
            await release_indexing.wait()
            documents.append(
                DocumentInfo(
                    filename=DEMO_DOCUMENT_FILENAME,
                    chunks_count=1,
                    is_demo_document=True,
                )
            )
            return 1, "EN"

        def delete_user_document(
            self, _user_id: str | None = None, filename: str = "", **_kwargs: object
        ) -> int:
            before = len(documents)
            documents[:] = [document for document in documents if document.filename != filename]
            return before - len(documents)

    class Limiter:
        async def acquire(self) -> bool:
            return True

        async def release(self) -> None:
            return None

    class StateFactory:
        def __new__(cls) -> _LifecycleState:
            return state

    monkeypatch.setattr(documents_router, "global_expensive_operation_limiter", Limiter())
    monkeypatch.setattr(documents_router, "DemoDocumentStateService", StateFactory)
    monkeypatch.setattr(
        "app.services.demo_document_service.DemoDocumentStateService", StateFactory
    )

    rag = RAG()
    storage = DocumentFileStorage(tmp_path)
    user_id = "router-race-user"
    seed = asyncio.create_task(documents_router.seed_demo_document(user_id, rag, storage))
    await started_indexing.wait()
    delete = asyncio.create_task(
        documents_router.delete_document(DEMO_DOCUMENT_FILENAME, user_id, rag, storage)
    )
    release_indexing.set()
    seed_result, delete_result = await asyncio.gather(seed, delete)
    reseed_result = await documents_router.seed_demo_document(user_id, rag, storage)

    assert seed_result.status == "seeded"
    assert delete_result.filename == DEMO_DOCUMENT_FILENAME
    assert reseed_result.status == "absent"
    assert state.deleted is True
    assert documents == []
    assert storage.get(user_id, DEMO_DOCUMENT_FILENAME) is None
