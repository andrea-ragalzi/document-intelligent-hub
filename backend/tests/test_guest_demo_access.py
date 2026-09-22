"""HTTP boundary tests for the anonymous shared demo workspace."""

from collections.abc import Generator
from threading import Lock
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from app.core.auth import DEMO_WORKSPACE_ID, firebase_principal_from_claims
from app.dependencies import (
    get_email_service,
    get_guest_query_budget_service,
    get_query_quota_service,
    get_rag_service,
)
from app.infrastructure.local_file_storage import get_document_file_storage
from app.schemas.rag_schema import DocumentInfo, FileFilterResponse
from app.services.document_file_storage import DocumentFileStorage
from app.services.guest_query_budget_service import (
    GuestBudgetStatus,
    GuestBudgetExceededError,
    GuestQueryBudgetService,
)
from app.services.query_concurrency_limiter import guest_query_concurrency_limiter
from app.services.query_quota_service import QueryQuotaReservation, QueryQuotaService
from app.services.rag_orchestrator_service import RAGService
from main import app


GUEST_UID = "anonymous-recruiter"
REGISTERED_UID = "registered-user"
AUTH_HEADER = {"Authorization": "Bearer test-token"}


@pytest.fixture
def guest_client(tmp_path) -> Generator[tuple[TestClient, Mock, Mock], None, None]:
    previous_overrides = app.dependency_overrides.copy()
    rag_service = Mock(spec=RAGService)
    registered_quota = Mock(spec=QueryQuotaService)
    registered_quota.reserve.return_value = QueryQuotaReservation("FREE", 20, 1)
    guest_budget = Mock(spec=GuestQueryBudgetService)
    guest_budget.reserve.return_value = QueryQuotaReservation("GUEST", 8, 1)
    guest_budget.get_status.return_value = GuestBudgetStatus(3, 8, 5, True)

    app.dependency_overrides.clear()
    app.dependency_overrides[get_rag_service] = lambda: rag_service
    app.dependency_overrides[get_query_quota_service] = lambda: registered_quota
    app.dependency_overrides[get_guest_query_budget_service] = lambda: guest_budget
    app.dependency_overrides[get_document_file_storage] = lambda: DocumentFileStorage(
        tmp_path / "originals"
    )
    client = TestClient(app)
    try:
        yield client, rag_service, guest_budget
    finally:
        client.close()
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous_overrides)


def _anonymous_claims() -> dict[str, object]:
    return {
        "uid": GUEST_UID,
        "firebase": {"sign_in_provider": "anonymous"},
    }


def _registered_claims() -> dict[str, object]:
    return {
        "uid": REGISTERED_UID,
        "email_verified": True,
        "firebase": {"sign_in_provider": "password"},
    }


def test_firebase_provider_claim_classifies_guest_and_registered_users() -> None:
    assert firebase_principal_from_claims(_anonymous_claims()).is_anonymous is True
    assert firebase_principal_from_claims(_registered_claims()).is_anonymous is False
    assert (
        firebase_principal_from_claims({"uid": "custom-token-user"}).is_anonymous
        is False
    )


def test_anonymous_token_lists_shared_demo_corpus(
    guest_client: tuple[TestClient, Mock, Mock],
) -> None:
    client, rag_service, _ = guest_client
    rag_service.get_user_documents.return_value = [
        DocumentInfo(
            filename=f"0{index}_InGen.pdf", chunks_count=2, is_demo_document=True
        )
        for index in range(1, 6)
    ]

    with patch("app.core.auth.auth.verify_id_token", return_value=_anonymous_claims()):
        response = client.get(
            "/rag/documents/list?user_id=registered-user", headers=AUTH_HEADER
        )

    assert response.status_code == 200
    assert response.json()["total_count"] == 5
    assert response.json()["user_id"] == DEMO_WORKSPACE_ID
    rag_service.get_user_documents.assert_called_once_with(DEMO_WORKSPACE_ID)


def test_anonymous_token_queries_real_rag_pipeline_in_demo_namespace(
    guest_client: tuple[TestClient, Mock, Mock],
) -> None:
    client, rag_service, guest_budget = guest_client
    rag_service.get_user_documents.return_value = [
        DocumentInfo(filename="01_InGen.pdf", chunks_count=2)
    ]
    rag_service.try_deterministic_query.return_value = None
    rag_service.answer_query.return_value = (
        "The shared corpus says so.",
        [{"filename": "01_InGen.pdf", "page_number": 2}],
    )

    with (
        patch("app.core.auth.auth.verify_id_token", return_value=_anonymous_claims()),
        patch(
            "app.routers.query_router.query_parser_service.extract_file_filters",
            return_value=FileFilterResponse(
                original_query="What does it say?", cleaned_query="What does it say?"
            ),
        ),
    ):
        response = client.post(
            "/rag/query/",
            headers=AUTH_HEADER,
            json={"query": "What does it say?", "conversation_history": []},
        )

    assert response.status_code == 200
    assert response.json()["citations"] == [
        {"filename": "01_InGen.pdf", "page_number": 2}
    ]
    assert rag_service.answer_query.call_args.args[1] == DEMO_WORKSPACE_ID
    guest_budget.reserve.assert_called_once()


def test_guest_can_read_a_demo_source_but_only_through_shared_namespace(
    guest_client: tuple[TestClient, Mock, Mock], tmp_path
) -> None:
    client, rag_service, _ = guest_client
    filename = "01_InGen.pdf"
    rag_service.get_user_documents.return_value = [
        DocumentInfo(filename=filename, chunks_count=2, is_demo_document=True)
    ]
    storage = DocumentFileStorage(tmp_path / "demo-originals")
    storage.store(DEMO_WORKSPACE_ID, filename, b"%PDF-1.4 synthetic")
    app.dependency_overrides[get_document_file_storage] = lambda: storage

    with patch("app.core.auth.auth.verify_id_token", return_value=_anonymous_claims()):
        response = client.get(
            f"/rag/documents/content?filename={filename}", headers=AUTH_HEADER
        )

    assert response.status_code == 200
    assert response.content == b"%PDF-1.4 synthetic"
    rag_service.get_user_documents.assert_called_once_with(DEMO_WORKSPACE_ID)


@pytest.mark.parametrize(
    ("method", "path", "kwargs"),
    [
        ("post", "/rag/documents/seed-demo", {}),
        (
            "post",
            "/rag/upload/",
            {"files": {"file": ("guest.pdf", b"%PDF-1.4", "application/pdf")}},
        ),
        ("delete", "/rag/documents/delete?filename=01_InGen.pdf", {}),
        ("delete", "/rag/documents/delete-all", {}),
        ("delete", "/rag/account/data", {}),
        ("post", "/rag/feedback/", {"json": {"message": "hello"}}),
        ("post", "/rag/report-bug/", {"data": {"description": "hello"}}),
        ("post", "/auth/refresh-claims?id_token=test-token", {}),
        ("post", "/rag/summarize/", {"json": {"conversation_history": []}}),
        ("post", "/auth/admin/set-tier?email=x%40example.com&tier=FREE", {}),
    ],
)
def test_guest_cannot_mutate_or_seed_documents(
    guest_client: tuple[TestClient, Mock, Mock],
    method: str,
    path: str,
    kwargs: dict[str, object],
) -> None:
    client, rag_service, _ = guest_client
    storage = Mock(spec=DocumentFileStorage)
    email_service = Mock()
    app.dependency_overrides[get_document_file_storage] = lambda: storage
    app.dependency_overrides[get_email_service] = lambda: email_service
    with patch("app.core.auth.auth.verify_id_token", return_value=_anonymous_claims()):
        response = getattr(client, method)(path, headers=AUTH_HEADER, **kwargs)

    assert response.status_code == 403
    rag_service.index_document.assert_not_called()
    rag_service.delete_user_document.assert_not_called()
    rag_service.delete_all_user_documents.assert_not_called()
    rag_service.generate_conversation_summary.assert_not_called()
    storage.store.assert_not_called()
    storage.delete.assert_not_called()
    storage.delete_all.assert_not_called()
    assert not email_service.method_calls


def test_guest_usage_is_authoritative_and_bound_to_verified_uid_and_client_ip(
    guest_client: tuple[TestClient, Mock, Mock],
) -> None:
    client, _, guest_budget = guest_client
    with patch("app.core.auth.auth.verify_id_token", return_value=_anonymous_claims()):
        response = client.get(
            "/auth/usage?user_id=registered-user",
            headers={**AUTH_HEADER, "X-Forwarded-For": "203.0.113.8"},
        )

    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "queries_today": 3,
        "query_limit": 8,
        "remaining": 5,
        "limited": True,
        "tier": "GUEST",
    }
    guest_budget.get_status.assert_called_once_with(GUEST_UID, "testclient")


def test_development_guest_usage_reports_unlimited_without_reading_storage(
    guest_client: tuple[TestClient, Mock, Mock],
) -> None:
    client, _, guest_budget = guest_client
    guest_budget.get_status.return_value = GuestBudgetStatus(0, None, None, False)

    with patch("app.core.auth.auth.verify_id_token", return_value=_anonymous_claims()):
        response = client.get("/auth/usage", headers=AUTH_HEADER)

    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "queries_today": 0,
        "query_limit": None,
        "remaining": None,
        "limited": False,
        "tier": "GUEST",
    }


@pytest.mark.parametrize("headers", [{}, AUTH_HEADER])
def test_missing_or_invalid_auth_never_reaches_rag(
    guest_client: tuple[TestClient, Mock, Mock], headers: dict[str, str]
) -> None:
    client, rag_service, guest_budget = guest_client
    verification = (
        patch("app.core.auth.auth.verify_id_token", side_effect=ValueError("invalid"))
        if headers
        else patch("app.core.auth.auth.verify_id_token")
    )
    with verification:
        response = client.post(
            "/rag/query/", headers=headers, json={"query": "What does the corpus say?"}
        )

    assert response.status_code == 401
    guest_budget.reserve.assert_not_called()
    rag_service.get_user_documents.assert_not_called()
    rag_service.answer_query.assert_not_called()


def test_guest_query_ignores_workspace_and_uid_injection(
    guest_client: tuple[TestClient, Mock, Mock],
) -> None:
    client, rag_service, _ = guest_client
    rag_service.get_user_documents.return_value = []
    rag_service.try_deterministic_query.return_value = None
    rag_service.answer_query.return_value = ("Safe answer", [])
    with (
        patch("app.core.auth.auth.verify_id_token", return_value=_anonymous_claims()),
        patch(
            "app.routers.query_router.query_parser_service.extract_file_filters",
            return_value=FileFilterResponse(
                original_query="Private question", cleaned_query="Private question"
            ),
        ),
    ):
        response = client.post(
            "/rag/query/?user_id=registered-user&workspace_id=registered-user",
            headers=AUTH_HEADER,
            json={
                "query": "Private question",
                "user_id": "registered-user",
                "workspace_id": "registered-user",
            },
        )

    assert response.status_code == 200
    assert rag_service.answer_query.call_args.args[1] == DEMO_WORKSPACE_ID


def test_spoofed_forwarded_for_from_untrusted_client_is_ignored(
    guest_client: tuple[TestClient, Mock, Mock],
) -> None:
    _, rag_service, guest_budget = guest_client
    rag_service.get_user_documents.return_value = []
    rag_service.try_deterministic_query.return_value = ("answer", [], "test", "test")
    with TestClient(app, client=("198.51.100.20", 12345)) as untrusted_client:
        with patch(
            "app.core.auth.auth.verify_id_token", return_value=_anonymous_claims()
        ):
            response = untrusted_client.post(
                "/rag/query/",
                headers={**AUTH_HEADER, "X-Forwarded-For": "203.0.113.99"},
                json={"query": "What does the corpus say?"},
            )

    assert response.status_code == 200
    guest_budget.reserve.assert_called_once_with(GUEST_UID, "198.51.100.20")


def test_trusted_proxy_supplies_client_ip_to_guest_budget(
    guest_client: tuple[TestClient, Mock, Mock],
) -> None:
    _, rag_service, guest_budget = guest_client
    rag_service.get_user_documents.return_value = []
    rag_service.try_deterministic_query.return_value = ("answer", [], "test", "test")
    with TestClient(app, client=("127.0.0.1", 12345)) as trusted_client:
        with patch(
            "app.core.auth.auth.verify_id_token", return_value=_anonymous_claims()
        ):
            response = trusted_client.post(
                "/rag/query/",
                headers={**AUTH_HEADER, "X-Forwarded-For": "203.0.113.10"},
                json={"query": "What does the corpus say?"},
            )

    assert response.status_code == 200
    guest_budget.reserve.assert_called_once_with(GUEST_UID, "203.0.113.10")


@pytest.mark.parametrize(
    "payload",
    [
        {"query": "x" * 4001},
        {"query": "valid question", "conversation_history": "malformed"},
        {
            "query": "valid question",
            "conversation_history": [{"role": "user", "content": "x" * 4001}],
        },
    ],
)
def test_malformed_guest_payload_is_rejected_before_quota_or_rag(
    guest_client: tuple[TestClient, Mock, Mock], payload: dict[str, object]
) -> None:
    client, rag_service, guest_budget = guest_client
    with patch("app.core.auth.auth.verify_id_token", return_value=_anonymous_claims()):
        response = client.post("/rag/query/", headers=AUTH_HEADER, json=payload)

    assert response.status_code == 422
    guest_budget.reserve.assert_not_called()
    rag_service.get_user_documents.assert_not_called()
    rag_service.answer_query.assert_not_called()


class _ScenarioUsageTracker:
    """Thread-safe external-store fake used through the real budget service."""

    def __init__(self) -> None:
        self.uid_counts: dict[str, int] = {}
        self.ip_counts: dict[str, int] = {}
        self.global_count = 0
        self.lock = Lock()

    def reserve(
        self,
        *,
        uid: str,
        ip_address: str,
        uid_limit: int,
        ip_limit: int,
        global_limit: int,
    ) -> tuple[bool, int, str | None]:
        with self.lock:
            uid_count = self.uid_counts.get(uid, 0)
            ip_count = self.ip_counts.get(ip_address, 0)
            if uid_count >= uid_limit:
                return False, uid_count, "uid"
            if ip_count >= ip_limit:
                return False, uid_count, "ip"
            if self.global_count >= global_limit:
                return False, uid_count, "global"
            self.uid_counts[uid] = uid_count + 1
            self.ip_counts[ip_address] = ip_count + 1
            self.global_count += 1
            return True, uid_count + 1, None

    def get_usage(self, *, uid: str, ip_address: str) -> tuple[int, int, int]:
        with self.lock:
            return (
                self.uid_counts.get(uid, 0),
                self.ip_counts.get(ip_address, 0),
                self.global_count,
            )


def test_abusive_client_sequence_reaches_uid_ip_then_global_limits_before_rag(
    guest_client: tuple[TestClient, Mock, Mock],
) -> None:
    _, rag_service, _ = guest_client
    budget = GuestQueryBudgetService(
        _ScenarioUsageTracker(), 2, 3, 5, daily_quotas_enabled=True
    )
    app.dependency_overrides[get_guest_query_budget_service] = lambda: budget
    rag_service.get_user_documents.return_value = []
    rag_service.try_deterministic_query.return_value = ("answer", [], "test", "test")

    def query(uid: str, ip_address: str) -> int:
        direct_client = TestClient(app, client=(ip_address, 12345))
        try:
            with patch(
                "app.core.auth.auth.verify_id_token",
                return_value={
                    "uid": uid,
                    "firebase": {"sign_in_provider": "anonymous"},
                },
            ):
                return direct_client.post(
                    "/rag/query/",
                    headers={"Authorization": f"Bearer {uid}"},
                    json={"query": "What does the corpus say?"},
                ).status_code
        finally:
            direct_client.close()

    assert [query("guest-a", "198.51.100.1") for _ in range(2)] == [200, 200]
    rag_calls = rag_service.get_user_documents.call_count
    assert query("guest-a", "198.51.100.1") == 429
    assert rag_service.get_user_documents.call_count == rag_calls

    assert query("guest-b", "198.51.100.1") == 200
    rag_calls = rag_service.get_user_documents.call_count
    assert query("guest-b", "198.51.100.1") == 429
    assert rag_service.get_user_documents.call_count == rag_calls

    assert query("guest-c", "198.51.100.2") == 200
    assert query("guest-d", "198.51.100.3") == 200
    rag_calls = rag_service.get_user_documents.call_count
    assert query("guest-e", "198.51.100.4") == 429
    assert rag_service.get_user_documents.call_count == rag_calls == 5


def test_development_guest_requests_bypass_daily_quotas_but_use_real_router(
    guest_client: tuple[TestClient, Mock, Mock],
) -> None:
    client, rag_service, _ = guest_client
    tracker = Mock()
    budget = GuestQueryBudgetService(
        tracker, 1, 1, 1, daily_quotas_enabled=False
    )
    app.dependency_overrides[get_guest_query_budget_service] = lambda: budget
    rag_service.get_user_documents.return_value = []
    rag_service.try_deterministic_query.return_value = ("answer", [], "test", "test")

    with patch("app.core.auth.auth.verify_id_token", return_value=_anonymous_claims()):
        responses = [
            client.post(
                "/rag/query/",
                headers=AUTH_HEADER,
                json={"query": "What does the corpus say?"},
            )
            for _ in range(4)
        ]

    assert [response.status_code for response in responses] == [200, 200, 200, 200]
    assert rag_service.get_user_documents.call_count == 4
    tracker.reserve.assert_not_called()


def test_registered_query_stays_in_private_uid_namespace(
    guest_client: tuple[TestClient, Mock, Mock],
) -> None:
    client, rag_service, guest_budget = guest_client
    rag_service.get_user_documents.return_value = []
    rag_service.try_deterministic_query.return_value = None
    rag_service.answer_query.return_value = ("Private answer", [])

    with (
        patch("app.core.auth.auth.verify_id_token", return_value=_registered_claims()),
        patch("app.core.auth.auth.get_user") as get_user,
        patch(
            "app.routers.query_router.query_parser_service.extract_file_filters",
            return_value=FileFilterResponse(
                original_query="Private question", cleaned_query="Private question"
            ),
        ),
    ):
        get_user.return_value.email_verified = True
        response = client.post(
            "/rag/query/",
            headers=AUTH_HEADER,
            json={"query": "Private question", "conversation_history": []},
        )

    assert response.status_code == 200
    assert rag_service.answer_query.call_args.args[1] == REGISTERED_UID
    guest_budget.reserve.assert_not_called()


def test_guest_budget_rejection_happens_before_rag_work(
    guest_client: tuple[TestClient, Mock, Mock],
) -> None:
    client, rag_service, guest_budget = guest_client
    guest_budget.reserve.side_effect = GuestBudgetExceededError("global demo budget")

    with patch("app.core.auth.auth.verify_id_token", return_value=_anonymous_claims()):
        response = client.post(
            "/rag/query/",
            headers=AUTH_HEADER,
            json={"query": "What does the corpus say?"},
        )

    assert response.status_code == 429
    rag_service.get_user_documents.assert_not_called()
    rag_service.answer_query.assert_not_called()


def test_guest_concurrency_rejection_happens_before_budget_or_rag(
    guest_client: tuple[TestClient, Mock, Mock],
) -> None:
    client, rag_service, guest_budget = guest_client
    guest_query_concurrency_limiter.active = guest_query_concurrency_limiter.maximum
    try:
        with patch(
            "app.core.auth.auth.verify_id_token", return_value=_anonymous_claims()
        ):
            response = client.post(
                "/rag/query/",
                headers=AUTH_HEADER,
                json={"query": "What does the corpus say?"},
            )
    finally:
        guest_query_concurrency_limiter.active = 0

    assert response.status_code == 429
    guest_budget.reserve.assert_not_called()
    rag_service.get_user_documents.assert_not_called()
    rag_service.answer_query.assert_not_called()
