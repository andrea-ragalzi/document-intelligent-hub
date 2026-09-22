"""Idempotent startup provisioning for the shared synthetic InGen corpus."""

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from app.core.auth import DEMO_WORKSPACE_ID
from app.ports.file_storage import FileStoragePort
from app.services.rag_orchestrator_service import RAGService

DEMO_CORPUS_VERSION = "ingen-v1"
DEMO_CORPUS_DIRECTORY = Path(__file__).resolve().parents[2] / "assets" / "ingen_demo"
DEMO_SUGGESTED_QUESTIONS = [
    "What control failures contributed to the 1993 Isla Nublar incident?",
    "How did the reproductive-risk finding change InGen's operating controls?",
    "Compare the 2015 governance of Isla Nublar and Isla Sorna.",
]


@dataclass(frozen=True)
class DemoCorpusDocument:
    """Stable identity and bundled source for one synthetic document."""

    document_id: str
    filename: str

    @property
    def path(self) -> Path:
        return DEMO_CORPUS_DIRECTORY / self.filename


DEMO_CORPUS_DOCUMENTS = (
    DemoCorpusDocument(
        "ING-CORP-001", "01_InGen_Corporate_Operations_and_Site_Directory.pdf"
    ),
    DemoCorpusDocument(
        "ING-SEC-204", "02_InGen_Asset_Containment_and_Emergency_Response_Standard.pdf"
    ),
    DemoCorpusDocument(
        "ING-GEN-118",
        "03_InGen_Genetic_Asset_Development_and_Reproductive_Risk_Review.pdf",
    ),
    DemoCorpusDocument(
        "ING-RISK-093", "04_InGen_Post_Incident_Review_Jurassic_Park_1993.pdf"
    ),
    DemoCorpusDocument(
        "ING-SITEB-310",
        "05_InGen_Isla_Sorna_Site_B_Legacy_Operations_and_Biosecurity_Review.pdf",
    ),
)

_corpus_lock = asyncio.Lock()


@dataclass
class _BundledUpload:
    content: bytes
    filename: str | None

    async def read(self) -> bytes:
        return self.content


class SharedDemoCorpusService:
    """Provision exactly one read-only corpus under a non-user namespace."""

    def __init__(self, rag_service: RAGService, storage: FileStoragePort) -> None:
        self.rag_service = rag_service
        self.storage = storage

    def _is_complete(self) -> bool:
        documents = self.rag_service.get_user_documents(DEMO_WORKSPACE_ID)
        present = {document.filename for document in documents}
        expected = {document.filename for document in DEMO_CORPUS_DOCUMENTS}
        return present == expected

    async def ensure_ready(self) -> Literal["ready", "seeded"]:
        """Index missing startup data once and repair incomplete corpus state."""
        async with _corpus_lock:
            if self._is_complete():
                self._backfill_originals()
                return "ready"

            self.rag_service.delete_all_user_documents(DEMO_WORKSPACE_ID)
            self.storage.delete_all(DEMO_WORKSPACE_ID)
            try:
                for document in DEMO_CORPUS_DOCUMENTS:
                    content = document.path.read_bytes()
                    await self.rag_service.index_document(
                        file=_BundledUpload(content, document.filename),
                        user_id=DEMO_WORKSPACE_ID,
                        document_language="EN",
                        document_metadata={
                            "is_demo_document": True,
                            "demo_document_id": document.document_id,
                            "demo_corpus_version": DEMO_CORPUS_VERSION,
                            "is_synthetic_demo": True,
                        },
                    )
                    self.storage.store(DEMO_WORKSPACE_ID, document.filename, content)
            except Exception:
                self.rag_service.delete_all_user_documents(DEMO_WORKSPACE_ID)
                self.storage.delete_all(DEMO_WORKSPACE_ID)
                raise
            return "seeded"

    def _backfill_originals(self) -> None:
        for document in DEMO_CORPUS_DOCUMENTS:
            if self.storage.get(DEMO_WORKSPACE_ID, document.filename) is None:
                self.storage.store(
                    DEMO_WORKSPACE_ID, document.filename, document.path.read_bytes()
                )
