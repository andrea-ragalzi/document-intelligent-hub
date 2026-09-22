"""One real, isolated PDF-to-Chroma upload integration check."""

from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory

from chromadb import PersistentClient
from fastapi.testclient import TestClient
from langchain_chroma import Chroma
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

from main import app
from app.core.auth import require_verified_registered_user
from app.dependencies import get_document_file_storage, get_rag_service
from app.db.chroma_client import COLLECTION_NAME, get_embedding_function
from app.infrastructure.local_file_storage import LocalFileStorage
from app.repositories.vector_store_repository import VectorStoreRepository
from app.services.query_expansion_service import QueryExpansionService
from app.services.rag_orchestrator_service import RAGService


class FakeLLM:
    def with_structured_output(self, _schema):
        return self

    def invoke(self, *_args, **_kwargs):
        raise AssertionError("upload must not call OpenAI")


class Translation:
    def translate(self, text, *_args):
        return text


def _pdf() -> bytes:
    writer = PdfWriter()
    page = writer.add_blank_page(612, 792)
    font = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        }
    )
    page[NameObject("/Resources")] = DictionaryObject(
        {NameObject("/Font"): DictionaryObject({NameObject("/F1"): font})}
    )
    stream = DecodedStreamObject()
    stream.set_data(
        b"BT /F1 12 Tf 72 720 Td (Synthetic medium policy document retention access controls) Tj ET"
    )
    page.replace_contents(stream)
    out = BytesIO()
    writer.write(out)
    return out.getvalue()


def test_real_upload_indexes_into_temporary_chroma(monkeypatch) -> None:
    with TemporaryDirectory() as directory:
        root = Path(directory)
        client = PersistentClient(path=str(root / "chroma"))
        store = Chroma(
            client=client,
            collection_name=COLLECTION_NAME,
            embedding_function=get_embedding_function(),
        )
        collection = client.get_or_create_collection(COLLECTION_NAME)
        repository = VectorStoreRepository(store, collection)
        service = RAGService(
            repository,
            FakeLLM(),
            FakeLLM(),
            Translation(),
            QueryExpansionService(FakeLLM()),
        )
        app.dependency_overrides[require_verified_registered_user] = lambda: (
            "synthetic-upload-user"
        )
        app.dependency_overrides[get_rag_service] = lambda: service
        app.dependency_overrides[get_document_file_storage] = lambda: LocalFileStorage(
            str(root / "originals")
        )
        monkeypatch.setattr(
            "app.routers.documents_router.check_file_count_limit", lambda *_: (True, 5)
        )
        monkeypatch.setattr(
            "app.routers.documents_router.get_max_upload_size_bytes",
            lambda *_: 10 * 1024 * 1024,
        )
        try:
            with TestClient(app) as test_client:
                response = test_client.post(
                    "/rag/upload/",
                    files={"file": ("medium.pdf", _pdf(), "application/pdf")},
                )
            assert response.status_code == 201, response.text
            assert response.json()["chunks_indexed"] > 0
            assert collection.count() > 0
        finally:
            app.dependency_overrides.clear()
