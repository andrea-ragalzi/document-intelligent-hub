"""ASGI regression tests for bounded multipart upload request bodies."""

import asyncio
from collections.abc import Callable, Coroutine
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

from app.config.security_constants import MAX_BUG_REPORT_REQUEST_SIZE
from main import UploadBodyLimitMiddleware, app


def _scope(path: str, headers: list[tuple[bytes, bytes]] | None = None) -> dict[str, Any]:
    return {
        "type": "http",
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "headers": headers or [(b"content-type", b"multipart/form-data; boundary=test")],
        "client": ("testclient", 50000),
        "server": ("testserver", 80),
    }


def _call_asgi(
    application: Callable[[dict[str, Any], Any, Any], Coroutine[Any, Any, None]],
    scope: dict[str, Any],
    chunks: list[bytes],
) -> tuple[list[dict[str, Any]], int]:
    sent: list[dict[str, Any]] = []
    next_chunk = 0
    receive_calls = 0

    async def receive() -> dict[str, Any]:
        nonlocal next_chunk, receive_calls
        receive_calls += 1
        if next_chunk >= len(chunks):
            return {"type": "http.disconnect"}
        body = chunks[next_chunk]
        next_chunk += 1
        return {
            "type": "http.request",
            "body": body,
            "more_body": next_chunk < len(chunks),
        }

    async def send(message: dict[str, Any]) -> None:
        sent.append(message)

    asyncio.run(application(scope, receive, send))
    return sent, receive_calls


def _response_status(sent: list[dict[str, Any]]) -> int:
    return int(
        next(message["status"] for message in sent if message["type"] == "http.response.start")
    )


def test_known_oversized_report_is_rejected_before_fastapi_parses_body() -> None:
    """A declared body above the transport limit never reaches multipart parsing."""
    headers = [
        (b"content-type", b"multipart/form-data; boundary=test"),
        (b"content-length", str(MAX_BUG_REPORT_REQUEST_SIZE + 1).encode()),
    ]
    with patch("starlette.formparsers.MultiPartParser.parse", new_callable=AsyncMock) as parse, patch(
        "app.services.rag_orchestrator_service.RAGService.index_document", new_callable=AsyncMock
    ) as index_document:
        sent, receive_calls = _call_asgi(app, _scope("/rag/report-bug/", headers), [b"x"])

    assert _response_status(sent) == 413
    assert receive_calls == 0
    parse.assert_not_awaited()
    index_document.assert_not_awaited()


def test_chunked_oversized_report_is_rejected_before_multipart_parser() -> None:
    """An absent Content-Length still cannot make the parser consume an oversized body."""
    with patch("starlette.formparsers.MultiPartParser.parse", new_callable=AsyncMock) as parse, patch(
        "app.services.rag_orchestrator_service.RAGService.index_document", new_callable=AsyncMock
    ) as index_document, patch("app.services.document_indexing_service.tempfile.mkstemp") as create_temp_file:
        sent, _ = _call_asgi(
            app,
            _scope("/rag/report-bug/"),
            [b"x" * MAX_BUG_REPORT_REQUEST_SIZE, b"x"],
        )

    assert _response_status(sent) == 413
    parse.assert_not_awaited()
    index_document.assert_not_awaited()
    create_temp_file.assert_not_called()


def test_report_body_at_exact_transport_limit_reaches_downstream() -> None:
    """The 64 KiB multipart allowance admits a request exactly at the body boundary."""
    downstream = Mock()
    received: list[bytes] = []

    async def application(_scope: dict[str, Any], receive: Any, send: Any) -> None:
        downstream()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                break
            received.append(message["body"])
            if not message.get("more_body", False):
                break
        await send({"type": "http.response.start", "status": 204, "headers": []})
        await send({"type": "http.response.body", "body": b""})

    middleware = UploadBodyLimitMiddleware(application)
    sent, _ = _call_asgi(
        middleware,
        _scope("/rag/report-bug/"),
        [b"x" * (MAX_BUG_REPORT_REQUEST_SIZE - 1), b"x"],
    )

    assert _response_status(sent) == 204
    assert sum(map(len, received)) == MAX_BUG_REPORT_REQUEST_SIZE
    downstream.assert_called_once()


def test_malformed_upload_content_length_is_a_controlled_client_error() -> None:
    """An invalid Content-Length is rejected without entering the multipart parser."""
    headers = [
        (b"content-type", b"multipart/form-data; boundary=test"),
        (b"content-length", b"not-a-number"),
    ]
    with patch("starlette.formparsers.MultiPartParser.parse", new_callable=AsyncMock) as parse:
        sent, _ = _call_asgi(app, _scope("/rag/detect-language/", headers), [b"x"])

    assert _response_status(sent) == 400
    parse.assert_not_awaited()


def test_non_upload_paths_are_not_limited_by_upload_body_guard() -> None:
    """The guard forwards non-upload requests without buffering or rejecting them."""
    downstream = Mock()

    async def application(_scope: dict[str, Any], _receive: Any, send: Any) -> None:
        downstream()
        await send({"type": "http.response.start", "status": 204, "headers": []})
        await send({"type": "http.response.body", "body": b""})

    sent, _ = _call_asgi(
        UploadBodyLimitMiddleware(application),
        _scope("/rag/query/"),
        [b"x" * (MAX_BUG_REPORT_REQUEST_SIZE + 1)],
    )

    assert _response_status(sent) == 204
    downstream.assert_called_once()
