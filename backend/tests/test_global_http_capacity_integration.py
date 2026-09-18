"""Small HTTP integration check for the global expensive-operation guard."""
import concurrent.futures
import threading
from unittest.mock import patch

from fastapi.testclient import TestClient
from fastapi import Request

from main import app
from app.core.auth import require_verified_email
from app.dependencies import get_query_quota_service, get_rag_service
from app.services.query_concurrency_limiter import global_expensive_operation_limiter


class Quota:
    def reserve(self, _user):
        return type("R", (), {"tier":"FREE", "reserved_count":1, "max_queries":20})()


class RAG:
    def __init__(self, started: threading.Event, release: threading.Event) -> None:
        self._started = started
        self._release = release
        self._lock = threading.Lock()
        self._active = 0

    def get_user_documents(self, _user): return []
    def answer_query(self, *_args, **_kwargs):
        with self._lock:
            self._active += 1
            if self._active == 2:
                self._started.set()
        assert self._release.wait(timeout=2)
        return "synthetic answer", []


def test_http_global_capacity_and_release() -> None:
    global_expensive_operation_limiter.active = 0
    both_started = threading.Event()
    release = threading.Event()
    rag = RAG(both_started, release)
    def synthetic_user(request: Request) -> str:
        return request.headers["x-user"]
    app.dependency_overrides[require_verified_email] = synthetic_user
    app.dependency_overrides[get_rag_service] = lambda: rag
    app.dependency_overrides[get_query_quota_service] = lambda: Quota()
    try:
        with patch("app.routers.query_router.query_parser_service.extract_file_filters", side_effect=lambda **kwargs: type("F", (), {"cleaned_query":kwargs["query"], "include_files":[], "exclude_files":[], "is_compound":False})()):
            def call(user):
                with TestClient(app) as client:
                    return client.post("/rag/query/", headers={"x-user": user}, json={"query":"retention policy"}).status_code
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
                first = pool.submit(call, "one")
                second = pool.submit(call, "two")
                assert both_started.wait(timeout=2)
                third = pool.submit(call, "three")
                assert third.result(timeout=2) == 429
                release.set()
                assert first.result(timeout=2) == 200
                assert second.result(timeout=2) == 200
            assert call("four") == 200
    finally:
        app.dependency_overrides.clear()
        global_expensive_operation_limiter.active = 0
