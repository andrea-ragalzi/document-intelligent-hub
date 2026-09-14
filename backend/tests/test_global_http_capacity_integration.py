"""Small HTTP integration check for the global expensive-operation guard."""
import concurrent.futures
import time
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
    def get_user_documents(self, _user): return []
    def answer_query(self, *_args, **_kwargs):
        time.sleep(.15)
        return "synthetic answer", []


def test_http_global_capacity_and_release() -> None:
    global_expensive_operation_limiter.active = 0
    def synthetic_user(request: Request) -> str:
        return request.headers["x-user"]
    app.dependency_overrides[require_verified_email] = synthetic_user
    app.dependency_overrides[get_rag_service] = lambda: RAG()
    app.dependency_overrides[get_query_quota_service] = lambda: Quota()
    try:
        with patch("app.routers.query_router.query_parser_service.extract_file_filters", side_effect=lambda **kwargs: type("F", (), {"cleaned_query":kwargs["query"], "include_files":[], "exclude_files":[], "is_compound":False})()):
            def call(user):
                with TestClient(app) as client:
                    return client.post("/rag/query/", headers={"x-user": user}, json={"query":"retention policy"}).status_code
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
                statuses=list(pool.map(call, ("one", "two", "three")))
            assert statuses.count(200) == 2
            assert statuses.count(429) == 1
            assert call("four") == 200
    finally:
        app.dependency_overrides.clear()
        global_expensive_operation_limiter.active = 0
