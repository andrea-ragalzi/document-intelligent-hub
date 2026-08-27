"""Focused tests for the PDF processing and indexing lifecycle."""

import os
from io import BytesIO
from unittest.mock import Mock, patch

import pytest
from fastapi import UploadFile
from langchain_core.documents import Document

from app.repositories.vector_store_repository import VectorStoreRepository
from app.services.document_classifier_service import DocumentCategory
from app.services.document_indexing_service import DocumentIndexingService


@pytest.fixture
def indexing_dependencies() -> tuple[Mock, Mock, Mock]:
    """Return isolated repository, language, and classifier boundaries."""
    repository = Mock(spec=VectorStoreRepository)
    language_service = Mock()
    classifier_service = Mock()
    classifier_service.classify_document.return_value = (
        DocumentCategory.INFORMATIVO_NON_STRUTTURATO
    )
    classifier_service.has_structural_density.return_value = False
    language_service.detect_language.return_value = "IT"
    return repository, language_service, classifier_service


@pytest.mark.asyncio
async def test_valid_pdf_is_chunked_and_indexed_with_owner_metadata(
    indexing_dependencies: tuple[Mock, Mock, Mock],
) -> None:
    """Parsed chunks must be ready for indexing and retain owner/file metadata."""
    repository, language_service, classifier_service = indexing_dependencies
    service = DocumentIndexingService(
        repository=repository,
        language_service=language_service,
        classifier_service=classifier_service,
    )
    upload = UploadFile(
        file=BytesIO(b"%PDF-1.4 deterministic test payload"),
        filename="handbook.pdf",
    )
    loaded_documents = [
        Document(
            page_content=(
                "Questo documento contiene abbastanza testo italiano per verificare "
                "il rilevamento della lingua e la preparazione dei metadati."
            ),
            metadata={"type": "NarrativeText", "page_number": 1},
        )
    ]
    loader = Mock()
    loader.load.return_value = loaded_documents

    with patch(
        "app.services.document_indexing_service.UnstructuredPDFLoader",
        return_value=loader,
    ) as loader_class:
        chunks_indexed, language = await service.index_document(
            upload,
            user_id="verified-user",
            document_metadata={"is_demo_document": True},
        )

    assert chunks_indexed > 0
    assert language == "IT"
    classifier_service.classify_document.assert_called_once()
    language_service.detect_language.assert_called_once()
    repository.add_documents.assert_called_once()

    indexed_chunks = repository.add_documents.call_args.args[0]
    assert len(indexed_chunks) == chunks_indexed
    assert all(chunk.page_content for chunk in indexed_chunks)
    assert all(chunk.metadata["source"] == "verified-user" for chunk in indexed_chunks)
    assert all(
        chunk.metadata["original_filename"] == "handbook.pdf"
        for chunk in indexed_chunks
    )
    assert all(
        chunk.metadata["original_language_code"] == "IT"
        for chunk in indexed_chunks
    )
    assert all("uploaded_at" in chunk.metadata for chunk in indexed_chunks)
    assert all(chunk.metadata["is_demo_document"] is True for chunk in indexed_chunks)

    temporary_pdf = loader_class.call_args.args[0]
    assert not os.path.exists(temporary_pdf)


@pytest.mark.asyncio
async def test_malformed_pdf_does_not_index_and_removes_temporary_file(
    indexing_dependencies: tuple[Mock, Mock, Mock],
) -> None:
    """A parser failure must not write chunks and must clean its temporary PDF."""
    repository, language_service, classifier_service = indexing_dependencies
    service = DocumentIndexingService(
        repository=repository,
        language_service=language_service,
        classifier_service=classifier_service,
    )
    upload = UploadFile(file=BytesIO(b"not a valid PDF"), filename="broken.pdf")
    loader = Mock()
    loader.load.side_effect = ValueError("malformed PDF")

    with patch(
        "app.services.document_indexing_service.UnstructuredPDFLoader",
        return_value=loader,
    ) as loader_class:
        with pytest.raises(ValueError, match="malformed PDF"):
            await service.index_document(upload, user_id="verified-user")

    repository.add_documents.assert_not_called()
    language_service.detect_language.assert_not_called()
    classifier_service.classify_document.assert_not_called()
    temporary_pdf = loader_class.call_args.args[0]
    assert not os.path.exists(temporary_pdf)
