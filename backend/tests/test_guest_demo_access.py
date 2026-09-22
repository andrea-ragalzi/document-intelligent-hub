"""HTTP boundary tests for the anonymous shared demo workspace."""

from collections.abc import Generator
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from app.core.auth import DEMO_WORKSPACE_ID
from app.dependencies import (
    get_guest_query_budget_service,
    get_query_quota_service,
    get_rag_service,
)
from app.infrastructure.local_file_storage import get_document_file_storage
from app.schemas.rag_schema import DocumentInfo, FileFilterResponse
from app.services.document_file_storage import DocumentFileStorage
from app.services.guest_query_budget_service import (
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
        ("get", "/auth/usage", {}),
        ("post", "/auth/refresh-claims?id_token=test-token", {}),
    ],
)
def test_guest_cannot_mutate_or_seed_documents(
    guest_client: tuple[TestClient, Mock, Mock],
    method: str,
    path: str,
    kwargs: dict[str, object],
) -> None:
    client, rag_service, _ = guest_client
    with patch("app.core.auth.auth.verify_id_token", return_value=_anonymous_claims()):
        response = getattr(client, method)(path, headers=AUTH_HEADER, **kwargs)

    assert response.status_code == 403
    rag_service.index_document.assert_not_called()
    rag_service.delete_user_document.assert_not_called()
    rag_service.delete_all_user_documents.assert_not_called()


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
