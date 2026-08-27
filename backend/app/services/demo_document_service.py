"""Private, idempotent starter-document seeding for authenticated users."""

import asyncio
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

from fastapi import UploadFile

from app.services.rag_orchestrator_service import RAGService

DEMO_DOCUMENT_FILENAME = "alice-cheshire-cat-demo.pdf"
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


async def _get_seed_lock(user_id: str) -> asyncio.Lock:
    async with _seed_locks_guard:
        return _seed_locks.setdefault(user_id, asyncio.Lock())


@dataclass(frozen=True)
class DemoSeedResult:
    status: str
    chunks_indexed: int


class DemoDocumentService:
    """Seeds the bundled PDF through the existing RAG indexing pipeline."""

    def __init__(self, rag_service: RAGService, document_path: Path = DEMO_DOCUMENT_PATH):
        self.rag_service = rag_service
        self.document_path = document_path

    async def seed_for_user(self, user_id: str) -> DemoSeedResult:
        """Create this user's private demo chunks once; never use a shared record."""
        lock = await _get_seed_lock(user_id)
        async with lock:
            if self.rag_service.user_document_exists(user_id, DEMO_DOCUMENT_FILENAME):
                return DemoSeedResult(status="ready", chunks_indexed=0)

            content = self.document_path.read_bytes()
            upload = UploadFile(
                file=BytesIO(content), filename=DEMO_DOCUMENT_FILENAME
            )
            chunks_indexed, _language = await self.rag_service.index_document(
                file=upload,
                user_id=user_id,
                document_language="EN",
                document_metadata={"is_demo_document": True},
            )
            return DemoSeedResult(status="seeded", chunks_indexed=chunks_indexed)
