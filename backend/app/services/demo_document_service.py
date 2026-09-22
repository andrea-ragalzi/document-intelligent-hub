"""Private, idempotent starter-document seeding for authenticated users."""

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from app.ports.file_storage import FileStoragePort
from app.services.rag_orchestrator_service import RAGService
from app.services.demo_document_state_service import DemoDocumentStateService

DEMO_DOCUMENT_FILENAME = "alices-adventures-in-wonderland.pdf"
LEGACY_DEMO_DOCUMENT_FILENAMES = ("alice-cheshire-cat-demo.pdf",)
DEMO_DOCUMENT_FILENAMES = (DEMO_DOCUMENT_FILENAME, *LEGACY_DEMO_DOCUMENT_FILENAMES)
DEMO_DOCUMENT_PATH = (
    Path(__file__).resolve().parents[2] / "assets" / DEMO_DOCUMENT_FILENAME
)
DEMO_SUGGESTED_QUESTIONS = [
    "What does Alice first notice about the Cheshire Cat?",
    "How is the Cheshire Cat described?",
    "What happens when the Cat disappears?",
]

_seed_locks: dict[str, asyncio.Lock] = {}
_seed_locks_guard = asyncio.Lock()


async def get_demo_document_lock(user_id: str) -> asyncio.Lock:
    async with _seed_locks_guard:
        return _seed_locks.setdefault(user_id, asyncio.Lock())


@dataclass(frozen=True)
class DemoSeedResult:
    status: Literal["seeded", "ready", "absent"]
    chunks_indexed: int


@dataclass
class _InMemoryUpload:
    """Minimal upload adapter for the bundled demo document."""

    content: bytes
    filename: str | None

    async def read(self) -> bytes:
        return self.content


class DemoDocumentService:
    """Seeds the bundled PDF through the existing RAG indexing pipeline."""

    def __init__(
        self,
        rag_service: RAGService,
        document_storage: FileStoragePort,
        document_path: Path = DEMO_DOCUMENT_PATH,
        state_service: DemoDocumentStateService | None = None,
    ):
        self.rag_service = rag_service
        self.document_storage = document_storage
        self.document_path = document_path
        self.state_service = state_service or DemoDocumentStateService()

    async def seed_for_user(self, user_id: str) -> DemoSeedResult:
        """Create this user's private demo chunks once; never use a shared record."""
        lock = await get_demo_document_lock(user_id)
        async with lock:
            # A missing document normally means a first seed is required.  An
            # explicit delete is different and must survive dashboard reloads.
            if self.state_service.is_deleted(user_id):
                return DemoSeedResult(status="absent", chunks_indexed=0)
            content = self.document_path.read_bytes()
            documents = self.rag_service.get_user_documents(user_id)
            demo_documents = (
                [document for document in documents if document.is_demo_document]
                if isinstance(documents, list)
                else []
            )
            current_demo = next(
                (
                    document
                    for document in demo_documents
                    if document.filename == DEMO_DOCUMENT_FILENAME
                ),
                None,
            )
            if current_demo is not None:
                # Earlier versions indexed the starter document but did not
                # retain its original. Backfill it so preview/download works
                # without reindexing.
                if self.document_storage.get(user_id, DEMO_DOCUMENT_FILENAME) is None:
                    self.document_storage.store(
                        user_id, DEMO_DOCUMENT_FILENAME, content
                    )
                return DemoSeedResult(status="ready", chunks_indexed=0)

            # A user upload with Alice's display filename is not the starter
            if self.rag_service.user_document_exists(user_id, DEMO_DOCUMENT_FILENAME):
                return DemoSeedResult(status="absent", chunks_indexed=0)

            legacy_documents = [
                document.filename
                for document in demo_documents
                if document.filename in LEGACY_DEMO_DOCUMENT_FILENAMES
            ]

            upload = _InMemoryUpload(
                content=content,
                filename=DEMO_DOCUMENT_FILENAME,
            )
            try:
                chunks_indexed, _language = await self.rag_service.index_document(
                    file=upload,
                    user_id=user_id,
                    document_language="EN",
                    document_metadata={"is_demo_document": True},
                )
                self.document_storage.store(user_id, DEMO_DOCUMENT_FILENAME, content)
                for legacy_filename in legacy_documents:
                    self.rag_service.delete_user_document(user_id, legacy_filename)
                    self.document_storage.delete(user_id, legacy_filename)
            except Exception:
                # Indexing implementations rollback their own failed batches,
                # but storing the original can fail after a successful index.
                # This idempotent cleanup covers both cases.
                self.rag_service.delete_user_document(user_id, DEMO_DOCUMENT_FILENAME)
                self.document_storage.delete(user_id, DEMO_DOCUMENT_FILENAME)
                raise
            return DemoSeedResult(status="seeded", chunks_indexed=chunks_indexed)
