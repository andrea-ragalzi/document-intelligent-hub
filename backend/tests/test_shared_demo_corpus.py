"""Idempotency and provenance tests for the shared InGen corpus."""

from unittest.mock import AsyncMock, Mock

import pytest
from pypdf import PdfReader

from app.core.auth import DEMO_WORKSPACE_ID
from app.schemas.rag_schema import DocumentInfo
from app.services.document_file_storage import DocumentFileStorage
from app.services.rag_orchestrator_service import RAGService
from app.services.shared_demo_corpus_service import (
    DEMO_CORPUS_DOCUMENTS,
    SharedDemoCorpusService,
)


def test_demo_corpus_contains_exactly_five_synthetic_ingen_pdfs() -> None:
    assert len(DEMO_CORPUS_DOCUMENTS) == 5
    assert len({document.document_id for document in DEMO_CORPUS_DOCUMENTS}) == 5
    assert len({document.filename for document in DEMO_CORPUS_DOCUMENTS}) == 5
    for document in DEMO_CORPUS_DOCUMENTS:
        assert document.document_id.startswith("ING-")
        assert document.path.read_bytes().startswith(b"%PDF")
        first_page = PdfReader(document.path).pages[0].extract_text()
        assert "fan-made, synthetic enterprise document" in first_page
        assert "NOT OFFICIAL FRANCHISE MATERIAL" in first_page


@pytest.mark.asyncio
async def test_corpus_is_ingested_once_and_reused_by_all_guests(tmp_path) -> None:
    rag_service = Mock(spec=RAGService)
    rag_service.get_user_documents.side_effect = [
        [],
        [
            DocumentInfo(
                filename=document.filename,
                chunks_count=2,
                is_demo_document=True,
            )
            for document in DEMO_CORPUS_DOCUMENTS
        ],
    ]
    rag_service.index_document = AsyncMock(return_value=(2, "EN"))
    storage = DocumentFileStorage(tmp_path)
    service = SharedDemoCorpusService(rag_service, storage)

    first = await service.ensure_ready()
    second = await service.ensure_ready()

    assert first == "seeded"
    assert second == "ready"
    assert rag_service.index_document.await_count == 5
    assert {
        call.kwargs["user_id"] for call in rag_service.index_document.await_args_list
    } == {DEMO_WORKSPACE_ID}
    for call, document in zip(
        rag_service.index_document.await_args_list, DEMO_CORPUS_DOCUMENTS, strict=True
    ):
        assert call.kwargs["document_metadata"] == {
            "is_demo_document": True,
            "demo_document_id": document.document_id,
            "demo_corpus_version": "ingen-v1",
            "is_synthetic_demo": True,
        }
