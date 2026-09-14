"""Regression coverage for bounded, killable upload PDF parsing."""

import asyncio
import multiprocessing
import os
import tempfile
from io import BytesIO
from unittest.mock import Mock

import pytest
from fastapi import HTTPException, UploadFile

from app.routers import documents_router
from app.services.document_indexing_service import DocumentIndexingService
from app.services.query_concurrency_limiter import (
    GlobalExpensiveOperationLimiter,
    QueryConcurrencyLimiter,
)


def _service() -> DocumentIndexingService:
    return DocumentIndexingService(Mock(), Mock(), Mock())


def _track_cleanup(
    service: DocumentIndexingService, monkeypatch: pytest.MonkeyPatch
) -> list[str]:
    paths: list[str] = []
    cleanup = service._cleanup_temp_file

    def tracked_cleanup(temp_file_path: str) -> None:
        paths.append(temp_file_path)
        cleanup(temp_file_path)

    monkeypatch.setattr(service, "_cleanup_temp_file", tracked_cleanup)
    return paths


def _preview_temp_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path: object
) -> str:
    descriptor, temp_file_path = tempfile.mkstemp(dir=str(tmp_path), suffix=".pdf")
    monkeypatch.setattr(
        "app.services.document_indexing_service.tempfile.mkstemp",
        lambda **_kwargs: (descriptor, temp_file_path),
    )
    return temp_file_path


@pytest.mark.asyncio
async def test_over_page_limit_rejects_before_unstructured_parsing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if multiprocessing.get_start_method() != "fork":
        pytest.skip("The deterministic worker stub requires fork semantics.")

    service = _service()
    parser_started = multiprocessing.Event()
    cleanup_paths = _track_cleanup(service, monkeypatch)

    class UnexpectedLoader:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            parser_started.set()

        def load(self) -> list[object]:
            return []

    monkeypatch.setattr(
        "app.services.document_indexing_service._get_pdf_page_count", lambda _path: 101
    )
    monkeypatch.setattr(
        "app.services.document_indexing_service.UnstructuredPDFLoader", UnexpectedLoader
    )

    with pytest.raises(ValueError, match="too many pages"):
        await service.index_document(
            UploadFile(file=BytesIO(b"%PDF"), filename="too-many-pages.pdf"), "user"
        )

    assert not parser_started.is_set()
    assert len(cleanup_paths) == 1
    assert not os.path.exists(cleanup_paths[0])


@pytest.mark.asyncio
async def test_blocked_unstructured_parser_is_terminated_on_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if multiprocessing.get_start_method() != "fork":
        pytest.skip("The deterministic worker stub requires fork semantics.")

    service = _service()
    parser_started = multiprocessing.Event()
    cleanup_paths = _track_cleanup(service, monkeypatch)

    class BlockingLoader:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            pass

        def load(self) -> list[object]:
            parser_started.set()
            multiprocessing.Event().wait()
            return []

    monkeypatch.setattr(
        "app.services.document_indexing_service._get_pdf_page_count", lambda _path: 1
    )
    monkeypatch.setattr(
        "app.services.document_indexing_service.UnstructuredPDFLoader", BlockingLoader
    )
    monkeypatch.setattr("app.services.document_indexing_service.PDF_PARSING_TIMEOUT_SECONDS", 0.05)

    with pytest.raises(TimeoutError, match="PDF parsing timed out"):
        await service.index_document(
            UploadFile(file=BytesIO(b"%PDF"), filename="blocked.pdf"), "user"
        )

    assert parser_started.is_set()
    assert len(cleanup_paths) == 1
    assert not os.path.exists(cleanup_paths[0])


@pytest.mark.asyncio
async def test_parser_error_removes_the_temporary_pdf(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if multiprocessing.get_start_method() != "fork":
        pytest.skip("The deterministic worker stub requires fork semantics.")

    service = _service()
    cleanup_paths = _track_cleanup(service, monkeypatch)

    class FailingLoader:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            pass

        def load(self) -> list[object]:
            raise RuntimeError("synthetic parser failure")

    monkeypatch.setattr(
        "app.services.document_indexing_service._get_pdf_page_count", lambda _path: 1
    )
    monkeypatch.setattr(
        "app.services.document_indexing_service.UnstructuredPDFLoader", FailingLoader
    )

    with pytest.raises(ValueError, match="Unable to parse PDF"):
        await service.index_document(
            UploadFile(file=BytesIO(b"%PDF"), filename="broken.pdf"), "user"
        )

    assert len(cleanup_paths) == 1
    assert not os.path.exists(cleanup_paths[0])


@pytest.mark.asyncio
async def test_language_preview_rejects_over_page_limit_and_removes_temp_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path: object
) -> None:
    if multiprocessing.get_start_method() != "fork":
        pytest.skip("The deterministic worker stub requires fork semantics.")

    service = _service()
    temp_file_path = _preview_temp_file(monkeypatch, tmp_path)
    loader_started = multiprocessing.Event()

    class UnexpectedLoader:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            loader_started.set()

        def load(self) -> list[object]:
            return []

    monkeypatch.setattr(
        "app.services.document_indexing_service._get_pdf_page_count", lambda _path: 101
    )
    monkeypatch.setattr(
        "app.services.document_indexing_service.UnstructuredPDFLoader", UnexpectedLoader
    )

    with pytest.raises(ValueError, match="too many pages"):
        await service.detect_document_language_preview(
            UploadFile(file=BytesIO(b"%PDF"), filename="too-many-pages.pdf")
        )

    assert not loader_started.is_set()
    assert not os.path.exists(temp_file_path)


@pytest.mark.asyncio
async def test_language_preview_timeout_terminates_parser_and_removes_temp_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path: object
) -> None:
    if multiprocessing.get_start_method() != "fork":
        pytest.skip("The deterministic worker stub requires fork semantics.")

    service = _service()
    temp_file_path = _preview_temp_file(monkeypatch, tmp_path)
    parser_started = multiprocessing.Event()

    class BlockingLoader:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            pass

        def load(self) -> list[object]:
            parser_started.set()
            multiprocessing.Event().wait()
            return []

    monkeypatch.setattr(
        "app.services.document_indexing_service._get_pdf_page_count", lambda _path: 1
    )
    monkeypatch.setattr(
        "app.services.document_indexing_service.UnstructuredPDFLoader", BlockingLoader
    )
    monkeypatch.setattr("app.services.document_indexing_service.PDF_PARSING_TIMEOUT_SECONDS", 0.05)

    with pytest.raises(TimeoutError, match="PDF parsing timed out"):
        await service.detect_document_language_preview(
            UploadFile(file=BytesIO(b"%PDF"), filename="blocked-preview.pdf")
        )

    assert parser_started.is_set()
    assert not os.path.exists(temp_file_path)


@pytest.mark.asyncio
async def test_language_preview_parser_error_removes_temp_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path: object
) -> None:
    if multiprocessing.get_start_method() != "fork":
        pytest.skip("The deterministic worker stub requires fork semantics.")

    service = _service()
    temp_file_path = _preview_temp_file(monkeypatch, tmp_path)

    class FailingLoader:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            pass

        def load(self) -> list[object]:
            raise RuntimeError("synthetic parser failure")

    monkeypatch.setattr(
        "app.services.document_indexing_service._get_pdf_page_count", lambda _path: 1
    )
    monkeypatch.setattr(
        "app.services.document_indexing_service.UnstructuredPDFLoader", FailingLoader
    )

    with pytest.raises(ValueError, match="Unable to parse PDF"):
        await service.detect_document_language_preview(
            UploadFile(file=BytesIO(b"%PDF"), filename="broken-preview.pdf")
        )

    assert not os.path.exists(temp_file_path)


@pytest.mark.asyncio
async def test_upload_releases_global_capacity_after_parser_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    global_limiter = GlobalExpensiveOperationLimiter(maximum=1)
    monkeypatch.setattr(documents_router, "global_expensive_operation_limiter", global_limiter)
    monkeypatch.setattr(documents_router, "upload_concurrency_limiter", QueryConcurrencyLimiter())

    async def upload_size_limits(*_args: object) -> tuple[int, float]:
        return 100, 1.0

    class TimedOutRAG:
        def user_document_exists(self, *_args: object) -> bool:
            return False

        async def index_document(self, **_kwargs: object) -> tuple[int, str]:
            raise TimeoutError("PDF parsing timed out.")

        def delete_user_document(self, *_args: object) -> int:
            return 0

    monkeypatch.setattr(documents_router, "_get_upload_size_limits", upload_size_limits)
    storage = Mock()

    with pytest.raises(HTTPException) as error:
        await documents_router.upload_document(
            None,
            UploadFile(file=BytesIO(b"%PDF"), filename="timeout.pdf"),
            "user",
            TimedOutRAG(),
            storage,
        )

    assert error.value.status_code == 500
    assert "PDF parsing" not in error.value.detail
    assert global_limiter.active == 0
    assert await global_limiter.acquire() is True
    await global_limiter.release()


@pytest.mark.asyncio
async def test_language_preview_cancellation_releases_both_limiters(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    global_limiter = GlobalExpensiveOperationLimiter(maximum=1)
    preview_limiter = QueryConcurrencyLimiter()
    started = asyncio.Event()
    never_release = asyncio.Event()
    monkeypatch.setattr(documents_router, "global_expensive_operation_limiter", global_limiter)
    monkeypatch.setattr(documents_router, "language_preview_concurrency_limiter", preview_limiter)
    monkeypatch.setattr(documents_router, "get_max_upload_size_bytes", lambda _uid: 100)

    class BlockingRAG:
        async def detect_document_language_preview(
            self, **_kwargs: object
        ) -> tuple[str, float]:
            started.set()
            await never_release.wait()
            return "EN", 0.9

    task = asyncio.create_task(
        documents_router.detect_document_language(
            UploadFile(file=BytesIO(b"%PDF"), filename="cancel.pdf"),
            "user",
            BlockingRAG(),
        )
    )
    await asyncio.wait_for(started.wait(), timeout=1)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    assert global_limiter.active == 0
    assert await preview_limiter.acquire("user") is True
    await preview_limiter.release("user")
