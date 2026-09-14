"""Deterministic global-capacity coverage for document-only expensive work."""

import asyncio
from dataclasses import dataclass
from io import BytesIO

import pytest
from fastapi import HTTPException, UploadFile

from app.routers import documents_router
from app.services.query_concurrency_limiter import (
    GlobalExpensiveOperationLimiter,
)


@dataclass(frozen=True)
class _SeedResult:
    status: str = "seeded"
    chunks_indexed: int = 1


@pytest.mark.asyncio
@pytest.mark.parametrize("endpoint", ["seed-demo", "detect-language"])
async def test_document_expensive_endpoints_reject_a_third_global_operation(
    monkeypatch: pytest.MonkeyPatch, endpoint: str
) -> None:
    """Two users may work, while a third receives the shared-capacity response."""
    limiter = GlobalExpensiveOperationLimiter(maximum=2)
    started = 0
    both_started = asyncio.Event()
    release = asyncio.Event()
    monkeypatch.setattr(documents_router, "global_expensive_operation_limiter", limiter)

    async def block() -> None:
        nonlocal started
        started += 1
        if started == 2:
            both_started.set()
        await release.wait()

    if endpoint == "seed-demo":
        class DemoService:
            def __init__(self, *_args: object) -> None:
                pass

            async def seed_for_user(self, _user_id: str) -> _SeedResult:
                await block()
                return _SeedResult()

        monkeypatch.setattr(documents_router, "DemoDocumentService", DemoService)
        first = asyncio.create_task(
            documents_router.seed_demo_document("first", object(), object())
        )
        second = asyncio.create_task(
            documents_router.seed_demo_document("second", object(), object())
        )
        third = documents_router.seed_demo_document("third", object(), object())
    else:
        class RAG:
            async def detect_document_language_preview(
                self, **_kwargs: object
            ) -> tuple[str, float]:
                await block()
                return "EN", 0.9

        monkeypatch.setattr(documents_router, "get_max_upload_size_bytes", lambda _uid: 100)
        first = asyncio.create_task(
            documents_router.detect_document_language(
                UploadFile(file=BytesIO(b"%PDF-first"), filename="first.pdf"),
                "first",
                RAG(),
            )
        )
        second = asyncio.create_task(
            documents_router.detect_document_language(
                UploadFile(file=BytesIO(b"%PDF-second"), filename="second.pdf"),
                "second",
                RAG(),
            )
        )
        third = documents_router.detect_document_language(
            UploadFile(file=BytesIO(b"%PDF-third"), filename="third.pdf"),
            "third",
            RAG(),
        )

    await asyncio.wait_for(both_started.wait(), timeout=1)
    with pytest.raises(HTTPException) as error:
        await third
    assert error.value.status_code == 429
    assert error.value.headers == {"Retry-After": "120"}

    release.set()
    await first
    await second
    assert limiter.active == 0
    assert await limiter.acquire() is True
    await limiter.release()


@pytest.mark.asyncio
@pytest.mark.parametrize("endpoint", ["seed-demo", "detect-language"])
async def test_document_global_capacity_is_released_after_handled_failure(
    monkeypatch: pytest.MonkeyPatch, endpoint: str
) -> None:
    limiter = GlobalExpensiveOperationLimiter(maximum=1)
    monkeypatch.setattr(documents_router, "global_expensive_operation_limiter", limiter)

    if endpoint == "seed-demo":
        class DemoService:
            def __init__(self, *_args: object) -> None:
                pass

            async def seed_for_user(self, _user_id: str) -> _SeedResult:
                raise RuntimeError("synthetic failure")

        monkeypatch.setattr(documents_router, "DemoDocumentService", DemoService)
        call = documents_router.seed_demo_document("user", object(), object())
    else:
        class RAG:
            async def detect_document_language_preview(
                self, **_kwargs: object
            ) -> tuple[str, float]:
                raise RuntimeError("synthetic failure")

        monkeypatch.setattr(documents_router, "get_max_upload_size_bytes", lambda _uid: 100)
        call = documents_router.detect_document_language(
            UploadFile(file=BytesIO(b"%PDF"), filename="document.pdf"), "user", RAG()
        )

    with pytest.raises(HTTPException) as error:
        await call
    assert error.value.status_code == 500
    assert limiter.active == 0
    assert await limiter.acquire() is True
    await limiter.release()


@pytest.mark.asyncio
@pytest.mark.parametrize("endpoint", ["seed-demo", "detect-language"])
async def test_document_global_capacity_is_released_after_cancellation(
    monkeypatch: pytest.MonkeyPatch, endpoint: str
) -> None:
    limiter = GlobalExpensiveOperationLimiter(maximum=1)
    started = asyncio.Event()
    never_release = asyncio.Event()
    monkeypatch.setattr(documents_router, "global_expensive_operation_limiter", limiter)

    async def block_forever() -> None:
        started.set()
        await never_release.wait()

    if endpoint == "seed-demo":
        class DemoService:
            def __init__(self, *_args: object) -> None:
                pass

            async def seed_for_user(self, _user_id: str) -> _SeedResult:
                await block_forever()
                return _SeedResult()

        monkeypatch.setattr(documents_router, "DemoDocumentService", DemoService)
        task = asyncio.create_task(
            documents_router.seed_demo_document("user", object(), object())
        )
    else:
        class RAG:
            async def detect_document_language_preview(
                self, **_kwargs: object
            ) -> tuple[str, float]:
                await block_forever()
                return "EN", 0.9

        monkeypatch.setattr(documents_router, "get_max_upload_size_bytes", lambda _uid: 100)
        task = asyncio.create_task(
            documents_router.detect_document_language(
                UploadFile(file=BytesIO(b"%PDF"), filename="document.pdf"), "user", RAG()
            )
        )

    await asyncio.wait_for(started.wait(), timeout=1)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert limiter.active == 0
    assert await limiter.acquire() is True
    await limiter.release()
