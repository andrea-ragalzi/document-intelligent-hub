"""Security boundary tests for Firebase authentication and tenant isolation."""

from collections.abc import Generator
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient
from firebase_admin import auth

from app.dependencies import get_query_quota_service, get_rag_service
from app.routers import query_router
from app.schemas.rag_schema import DocumentInfo, FileFilterResponse
from app.services.document_file_storage import (
    DocumentFileStorage,
    get_document_file_storage,
)
from app.services.demo_document_service import DEMO_DOCUMENT_FILENAME
from app.services.demo_document_state_service import DemoDocumentStateService
from app.services.query_quota_service import (
    QueryLimitExceededError,
    QueryQuotaReservation,
    QueryQuotaService,
)
from app.services.rag_orchestrator_service import RAGService
from main import app


AUTHENTICATED_USER = "user-a"
OTHER_USER = "user-b"
VALID_AUTH_HEADER = {"Authorization": "Bearer verified-user-a-token"}


@pytest.fixture
def protected_client(tmp_path) -> Generator[tuple[TestClient, Mock], None, None]:
    """Use real authentication with a fake RAG service and no app lifespan."""
    previous_overrides = app.dependency_overrides.copy()
    rag_service = Mock(spec=RAGService)
    quota_service = Mock(spec=QueryQuotaService)
    quota_service.reserve.return_value = QueryQuotaReservation("FREE", 20, 1)
    rag_service.query_quota_service = quota_service

    app.dependency_overrides.clear()
    app.dependency_overrides[get_rag_service] = lambda: rag_service
    app.dependency_overrides[get_query_quota_service] = lambda: quota_service
    app.dependency_overrides[get_document_file_storage] = lambda: DocumentFileStorage(
        tmp_path / "document-originals"
    )
    client = TestClient(app)

    try:
        yield client, rag_service
    finally:
        client.close()
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous_overrides)


def test_protected_route_rejects_missing_authentication(
    protected_client: tuple[TestClient, Mock],
) -> None:
    """A protected document operation must reject requests without a token."""
    client, rag_service = protected_client

    with patch("app.core.auth.auth.verify_id_token") as verify_id_token:
        response = client.get("/rag/documents/list")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    verify_id_token.assert_not_called()
    rag_service.get_user_documents.assert_not_called()


def test_protected_route_rejects_malformed_authorization_header(
    protected_client: tuple[TestClient, Mock],
) -> None:
    """A non-Bearer authorization scheme must not reach Firebase or the service."""
    client, rag_service = protected_client

    with patch("app.core.auth.auth.verify_id_token") as verify_id_token:
        response = client.get(
            "/rag/documents/list",
            headers={"Authorization": "Token malformed"},
        )

    assert response.status_code == 401
    verify_id_token.assert_not_called()
    rag_service.get_user_documents.assert_not_called()


def test_protected_route_rejects_invalid_firebase_token(
    protected_client: tuple[TestClient, Mock],
) -> None:
    """A Bearer token rejected by Firebase must not reach protected operations."""
    client, rag_service = protected_client

    with patch(
        "app.core.auth.auth.verify_id_token",
        side_effect=auth.InvalidIdTokenError("invalid token"),
    ) as verify_id_token:
        response = client.get(
            "/rag/documents/list",
            headers={"Authorization": "Bearer invalid-token"},
        )

    assert response.status_code == 401
    verify_id_token.assert_called_once_with("invalid-token")
    rag_service.get_user_documents.assert_not_called()


def test_document_list_uses_verified_uid_and_ignores_spoofed_user_id(
    protected_client: tuple[TestClient, Mock],
) -> None:
    """The document list must be scoped to the Firebase UID, not client input."""
    client, rag_service = protected_client
    rag_service.get_user_documents.side_effect = lambda user_id: [
        DocumentInfo(filename=f"{user_id}.pdf", chunks_count=1, language="EN")
    ]

    with patch(
        "app.core.auth.auth.verify_id_token",
        return_value={"uid": AUTHENTICATED_USER},
    ):
        response = client.get(
            "/rag/documents/list",
            params={"user_id": OTHER_USER},
            headers=VALID_AUTH_HEADER,
        )

    assert response.status_code == 200
    assert response.json() == {
        "documents": [
            {
                "filename": f"{AUTHENTICATED_USER}.pdf",
                "chunks_count": 1,
                "language": "EN",
                "uploaded_at": None,
                "original_available": False,
                "is_demo_document": False,
            }
        ],
        "total_count": 1,
        "user_id": AUTHENTICATED_USER,
    }
    rag_service.get_user_documents.assert_called_once_with(AUTHENTICATED_USER)


def test_demo_seed_uses_verified_uid_and_ignores_spoofed_user_id(
    protected_client: tuple[TestClient, Mock],
) -> None:
    """Demo chunks must be seeded for the Firebase UID, never a request parameter."""
    client, rag_service = protected_client
    rag_service.user_document_exists.return_value = False
    rag_service.index_document = AsyncMock(return_value=(4, "EN"))

    with patch(
        "app.core.auth.auth.verify_id_token",
        return_value={"uid": AUTHENTICATED_USER},
    ):
        response = client.post(
            "/rag/documents/seed-demo",
            params={"user_id": OTHER_USER},
            headers=VALID_AUTH_HEADER,
        )

    assert response.status_code == 200
    assert response.json()["status"] == "seeded"
    assert response.json()["filename"] == DEMO_DOCUMENT_FILENAME
    assert response.json()["suggested_questions"] == [
        "What does Alice first notice about the Cheshire Cat?",
        "How is the Cheshire Cat described?",
        "What happens when the Cat disappears?",
    ]
    rag_service.user_document_exists.assert_any_call(
        AUTHENTICATED_USER, DEMO_DOCUMENT_FILENAME
    )
    assert rag_service.index_document.await_args.kwargs["user_id"] == AUTHENTICATED_USER


def test_delete_cannot_target_another_user_via_client_user_id(
    protected_client: tuple[TestClient, Mock],
) -> None:
    """A spoofed user ID must not let one user delete another user's chunks."""
    client, rag_service = protected_client
    stored_chunks = {(OTHER_USER, "shared.pdf"): 2}

    def delete_owned_document(user_id: str, filename: str) -> int:
        return stored_chunks.pop((user_id, filename), 0)

    rag_service.delete_user_document.side_effect = delete_owned_document

    with patch(
        "app.core.auth.auth.verify_id_token",
        return_value={"uid": AUTHENTICATED_USER},
    ):
        response = client.delete(
            "/rag/documents/delete",
            params={"filename": "shared.pdf", "user_id": OTHER_USER},
            headers=VALID_AUTH_HEADER,
        )

    assert response.status_code == 404
    assert stored_chunks == {(OTHER_USER, "shared.pdf"): 2}
    rag_service.delete_user_document.assert_called_once_with(
        user_id=AUTHENTICATED_USER,
        filename="shared.pdf",
    )


def test_delete_alice_uses_normal_deletion_and_persists_dismissal(
    protected_client: tuple[TestClient, Mock], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Alice follows the same storage/vector deletion path as any user PDF."""
    client, rag_service = protected_client
    rag_service.delete_user_document.return_value = 4
    rag_service.get_user_documents.return_value = [
        DocumentInfo(
            filename=DEMO_DOCUMENT_FILENAME,
            chunks_count=4,
            is_demo_document=True,
        )
    ]
    state_service = Mock(spec=DemoDocumentStateService)
    monkeypatch.setattr(
        "app.routers.documents_router.DemoDocumentStateService",
        lambda: state_service,
    )

    with patch(
        "app.core.auth.auth.verify_id_token",
        return_value={"uid": AUTHENTICATED_USER},
    ):
        response = client.delete(
            "/rag/documents/delete",
            params={"filename": DEMO_DOCUMENT_FILENAME},
            headers=VALID_AUTH_HEADER,
        )

    assert response.status_code == 200
    assert response.json()["chunks_deleted"] == 4
    rag_service.delete_user_document.assert_called_once_with(
        user_id=AUTHENTICATED_USER, filename=DEMO_DOCUMENT_FILENAME
    )
    state_service.mark_deleted.assert_called_once_with(AUTHENTICATED_USER)


def test_demo_tombstone_failure_leaves_alice_intact(
    protected_client: tuple[TestClient, Mock], monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    """A failed dismissal write must prevent every destructive Alice operation."""
    client, rag_service = protected_client
    storage = DocumentFileStorage(tmp_path / "originals")
    storage.store(AUTHENTICATED_USER, DEMO_DOCUMENT_FILENAME, b"%PDF-1.4 Alice")
    app.dependency_overrides[get_document_file_storage] = lambda: storage
    rag_service.get_user_documents.return_value = [
        DocumentInfo(
            filename=DEMO_DOCUMENT_FILENAME,
            chunks_count=4,
            is_demo_document=True,
        )
    ]
    state_service = Mock(spec=DemoDocumentStateService)
    state_service.mark_deleted.side_effect = OSError("Firestore unavailable")
    monkeypatch.setattr(
        "app.routers.documents_router.DemoDocumentStateService",
        lambda: state_service,
    )

    with patch("app.core.auth.auth.verify_id_token", return_value={"uid": AUTHENTICATED_USER}):
        response = client.delete(
            "/rag/documents/delete",
            params={"filename": DEMO_DOCUMENT_FILENAME},
            headers=VALID_AUTH_HEADER,
        )

    assert response.status_code == 500
    assert storage.get(AUTHENTICATED_USER, DEMO_DOCUMENT_FILENAME) is not None
    rag_service.delete_user_document.assert_not_called()


def test_same_named_user_upload_is_not_marked_as_demo_deletion(
    protected_client: tuple[TestClient, Mock], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Filename alone cannot turn a normal upload into Alice."""
    client, rag_service = protected_client
    rag_service.delete_user_document.return_value = 2
    rag_service.get_user_documents.return_value = [
        DocumentInfo(
            filename=DEMO_DOCUMENT_FILENAME,
            chunks_count=2,
            is_demo_document=False,
        )
    ]
    def unavailable_state_service() -> DemoDocumentStateService:
        raise OSError("Firestore unavailable")

    monkeypatch.setattr(
        "app.routers.documents_router.DemoDocumentStateService",
        unavailable_state_service,
    )

    with patch("app.core.auth.auth.verify_id_token", return_value={"uid": AUTHENTICATED_USER}):
        response = client.delete(
            "/rag/documents/delete",
            params={"filename": DEMO_DOCUMENT_FILENAME},
            headers=VALID_AUTH_HEADER,
        )

    assert response.status_code == 200


def test_legacy_demo_delete_persists_dismissal(
    protected_client: tuple[TestClient, Mock], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Legacy Alice metadata remains sufficient to preserve an explicit delete."""
    client, rag_service = protected_client
    legacy_filename = "alice-cheshire-cat-demo.pdf"
    rag_service.delete_user_document.return_value = 3
    rag_service.get_user_documents.return_value = [
        DocumentInfo(filename=legacy_filename, chunks_count=3, is_demo_document=True)
    ]
    state_service = Mock(spec=DemoDocumentStateService)
    monkeypatch.setattr(
        "app.routers.documents_router.DemoDocumentStateService",
        lambda: state_service,
    )

    with patch("app.core.auth.auth.verify_id_token", return_value={"uid": AUTHENTICATED_USER}):
        response = client.delete(
            "/rag/documents/delete",
            params={"filename": legacy_filename},
            headers=VALID_AUTH_HEADER,
        )

    assert response.status_code == 200
    state_service.mark_deleted.assert_called_once_with(AUTHENTICATED_USER)


def test_original_only_legacy_filename_without_provenance_is_ordinary(
    protected_client: tuple[TestClient, Mock], monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    """A legacy filename alone is insufficient to identify Alice."""
    client, rag_service = protected_client
    legacy_filename = "alice-cheshire-cat-demo.pdf"
    storage = DocumentFileStorage(tmp_path / "originals")
    storage.store(AUTHENTICATED_USER, legacy_filename, b"%PDF-1.4 old Alice")
    app.dependency_overrides[get_document_file_storage] = lambda: storage
    rag_service.get_user_documents.return_value = []
    rag_service.delete_user_document.return_value = 0
    state_service = Mock(spec=DemoDocumentStateService)
    monkeypatch.setattr(
        "app.routers.documents_router.DemoDocumentStateService",
        lambda: state_service,
    )

    with patch("app.core.auth.auth.verify_id_token", return_value={"uid": AUTHENTICATED_USER}):
        response = client.delete(
            "/rag/documents/delete",
            params={"filename": legacy_filename},
            headers=VALID_AUTH_HEADER,
        )

    assert response.status_code == 200
    assert storage.get(AUTHENTICATED_USER, legacy_filename) is None
    state_service.mark_deleted.assert_not_called()


def test_original_only_current_demo_delete_persists_dismissal(
    protected_client: tuple[TestClient, Mock], monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    """The bundled-PDF digest identifies a current original when vectors are gone."""
    from app.services.demo_document_service import DEMO_DOCUMENT_PATH

    client, rag_service = protected_client
    storage = DocumentFileStorage(tmp_path / "originals")
    storage.store(AUTHENTICATED_USER, DEMO_DOCUMENT_FILENAME, DEMO_DOCUMENT_PATH.read_bytes())
    app.dependency_overrides[get_document_file_storage] = lambda: storage
    rag_service.get_user_documents.return_value = []
    rag_service.delete_user_document.return_value = 0
    state_service = Mock(spec=DemoDocumentStateService)
    monkeypatch.setattr(
        "app.routers.documents_router.DemoDocumentStateService",
        lambda: state_service,
    )

    with patch("app.core.auth.auth.verify_id_token", return_value={"uid": AUTHENTICATED_USER}):
        response = client.delete(
            "/rag/documents/delete",
            params={"filename": DEMO_DOCUMENT_FILENAME},
            headers=VALID_AUTH_HEADER,
        )

    assert response.status_code == 200
    assert storage.get(AUTHENTICATED_USER, DEMO_DOCUMENT_FILENAME) is None
    state_service.mark_deleted.assert_called_once_with(AUTHENTICATED_USER)


def test_original_only_legacy_demo_content_delete_persists_dismissal(
    protected_client: tuple[TestClient, Mock], monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    """A legacy filename remains compatible when its original is the bundled PDF."""
    from app.services.demo_document_service import DEMO_DOCUMENT_PATH

    client, rag_service = protected_client
    legacy_filename = "alice-cheshire-cat-demo.pdf"
    storage = DocumentFileStorage(tmp_path / "originals")
    storage.store(AUTHENTICATED_USER, legacy_filename, DEMO_DOCUMENT_PATH.read_bytes())
    app.dependency_overrides[get_document_file_storage] = lambda: storage
    rag_service.get_user_documents.return_value = []
    rag_service.delete_user_document.return_value = 0
    state_service = Mock(spec=DemoDocumentStateService)
    monkeypatch.setattr(
        "app.routers.documents_router.DemoDocumentStateService",
        lambda: state_service,
    )

    with patch("app.core.auth.auth.verify_id_token", return_value={"uid": AUTHENTICATED_USER}):
        response = client.delete(
            "/rag/documents/delete",
            params={"filename": legacy_filename},
            headers=VALID_AUTH_HEADER,
        )

    assert response.status_code == 200
    assert storage.get(AUTHENTICATED_USER, legacy_filename) is None
    state_service.mark_deleted.assert_called_once_with(AUTHENTICATED_USER)


def test_bulk_delete_of_legacy_filename_without_provenance_does_not_dismiss_alice(
    protected_client: tuple[TestClient, Mock], monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    """Bulk deletion of a normal legacy-named upload does not dismiss Alice."""
    client, rag_service = protected_client
    legacy_filename = "alice-cheshire-cat-demo.pdf"
    storage = DocumentFileStorage(tmp_path / "originals")
    storage.store(AUTHENTICATED_USER, legacy_filename, b"%PDF-1.4 old Alice")
    app.dependency_overrides[get_document_file_storage] = lambda: storage
    rag_service.get_user_documents.return_value = []
    rag_service.delete_all_user_documents.return_value = 1
    state_service = Mock(spec=DemoDocumentStateService)
    monkeypatch.setattr(
        "app.routers.documents_router.DemoDocumentStateService",
        lambda: state_service,
    )

    with patch("app.core.auth.auth.verify_id_token", return_value={"uid": AUTHENTICATED_USER}):
        response = client.delete("/rag/documents/delete-all", headers=VALID_AUTH_HEADER)

    assert response.status_code == 200
    state_service.mark_deleted.assert_not_called()


def test_document_content_uses_verified_uid_not_client_user_id(
    protected_client: tuple[TestClient, Mock], tmp_path,
) -> None:
    """Original PDF access is scoped to the Firebase UID in the token."""
    client, rag_service = protected_client
    storage = DocumentFileStorage(tmp_path)
    storage.store(AUTHENTICATED_USER, "private.pdf", b"%PDF-1.4 owner")
    rag_service.get_user_documents.return_value = [
        DocumentInfo(filename="private.pdf", chunks_count=1, language="EN")
    ]
    rag_service.user_document_exists.return_value = False
    app.dependency_overrides[get_document_file_storage] = lambda: storage

    try:
        with patch(
            "app.core.auth.auth.verify_id_token",
            return_value={"uid": AUTHENTICATED_USER},
        ):
            response = client.get(
                "/rag/documents/content",
                params={"filename": "private.pdf", "user_id": OTHER_USER},
                headers=VALID_AUTH_HEADER,
            )
    finally:
        app.dependency_overrides.pop(get_document_file_storage, None)

    assert response.status_code == 200
    assert response.content == b"%PDF-1.4 owner"
    assert "inline" in response.headers["content-disposition"]
    rag_service.get_user_documents.assert_called_once_with(AUTHENTICATED_USER)
    rag_service.user_document_exists.assert_not_called()


def test_document_content_rejects_unauthenticated_requests(
    protected_client: tuple[TestClient, Mock],
) -> None:
    """A browser cannot retrieve an original merely by knowing its filename."""
    client, rag_service = protected_client

    with patch("app.core.auth.auth.verify_id_token") as verify_id_token:
        response = client.get("/rag/documents/content", params={"filename": "private.pdf"})

    assert response.status_code == 401
    verify_id_token.assert_not_called()
    rag_service.user_document_exists.assert_not_called()


def test_document_content_does_not_read_unowned_filenames(
    protected_client: tuple[TestClient, Mock],
) -> None:
    """A requested name outside the authenticated user's list cannot reach storage."""
    client, rag_service = protected_client
    document_storage = Mock(spec=DocumentFileStorage)
    rag_service.get_user_documents.return_value = [
        DocumentInfo(filename="owned.pdf", chunks_count=1, language="EN")
    ]
    app.dependency_overrides[get_document_file_storage] = lambda: document_storage

    try:
        with patch(
            "app.core.auth.auth.verify_id_token",
            return_value={"uid": AUTHENTICATED_USER},
        ):
            response = client.get(
                "/rag/documents/content",
                params={"filename": "unowned.pdf"},
                headers=VALID_AUTH_HEADER,
            )
    finally:
        app.dependency_overrides.pop(get_document_file_storage, None)

    assert response.status_code == 404
    document_storage.get.assert_not_called()


def test_document_content_rejects_files_outside_storage_root(
    protected_client: tuple[TestClient, Mock], tmp_path,
) -> None:
    """A storage defect cannot make an external file available to a user."""
    client, rag_service = protected_client
    storage = DocumentFileStorage(tmp_path / "originals")
    outside_file = tmp_path / "outside.pdf"
    outside_file.write_bytes(b"%PDF-1.4 outside")
    storage.get = Mock(return_value=outside_file)  # type: ignore[method-assign]
    rag_service.get_user_documents.return_value = [
        DocumentInfo(filename="owned.pdf", chunks_count=1, language="EN")
    ]
    app.dependency_overrides[get_document_file_storage] = lambda: storage

    try:
        with patch(
            "app.core.auth.auth.verify_id_token",
            return_value={"uid": AUTHENTICATED_USER},
        ):
            response = client.get(
                "/rag/documents/content",
                params={"filename": "owned.pdf"},
                headers=VALID_AUTH_HEADER,
            )
    finally:
        app.dependency_overrides.pop(get_document_file_storage, None)

    assert response.status_code == 404


def test_query_uses_verified_uid_and_ignores_spoofed_user_id(
    protected_client: tuple[TestClient, Mock],
) -> None:
    """RAG discovery and answer generation must both receive the verified UID."""
    client, rag_service = protected_client
    rag_service.get_user_documents.return_value = [
        DocumentInfo(filename="user-a.pdf", chunks_count=1, language="EN")
    ]
    rag_service.answer_query.return_value = ("Scoped answer", ["user-a.pdf"])

    quota_service = rag_service.query_quota_service
    parsed_query = FileFilterResponse(
        include_files=[],
        exclude_files=[],
        original_query="Private question",
        cleaned_query="Private question",
    )

    with patch(
        "app.core.auth.auth.verify_id_token",
        return_value={"uid": AUTHENTICATED_USER},
    ), patch.object(
        query_router.query_parser_service,
        "extract_file_filters",
        return_value=parsed_query,
    ):
        response = client.post(
            "/rag/query/",
            headers=VALID_AUTH_HEADER,
            json={"query": "Private question", "user_id": OTHER_USER},
        )

    assert response.status_code == 200
    assert response.json()["source_documents"] == ["user-a.pdf"]
    rag_service.get_user_documents.assert_called_once_with(AUTHENTICATED_USER)
    rag_service.answer_query.assert_called_once_with(
        "Private question",
        AUTHENTICATED_USER,
        [],
        None,
        include_files=None,
        exclude_files=None,
        raw_user_query="Private question",
    )
    quota_service.reserve.assert_called_once_with(AUTHENTICATED_USER)


def test_query_limit_rejection_happens_before_rag_work(
    protected_client: tuple[TestClient, Mock],
) -> None:
    """A rejected reservation must not reach document lookup or OpenAI/RAG work."""
    client, rag_service = protected_client
    quota_service = rag_service.query_quota_service
    quota_service.reserve.side_effect = QueryLimitExceededError(20, 20)

    with patch(
        "app.core.auth.auth.verify_id_token",
        return_value={"uid": AUTHENTICATED_USER},
    ):
        response = client.post(
            "/rag/query/",
            headers=VALID_AUTH_HEADER,
            json={"query": "Private question"},
        )

    assert response.status_code == 429
    quota_service.reserve.assert_called_once_with(AUTHENTICATED_USER)
    rag_service.get_user_documents.assert_not_called()
    rag_service.answer_query.assert_not_called()


def test_rag_error_response_and_logs_redact_exception_details(
    protected_client: tuple[TestClient, Mock],
) -> None:
    """OpenAI/RAG exception text must remain server-internal and redacted."""
    client, rag_service = protected_client
    secret_like_text = "sk-prohibited-test-value"
    private_query = "PRIVATE_QUERY_DO_NOT_LOG"
    rag_service.get_user_documents.return_value = []
    rag_service.answer_query.side_effect = RuntimeError(
        f"OpenAI request failed with {secret_like_text}"
    )
    parsed_query = FileFilterResponse(
        include_files=[],
        exclude_files=[],
        original_query=private_query,
        cleaned_query=private_query,
    )
    router_logger = Mock()

    with patch(
        "app.core.auth.auth.verify_id_token",
        return_value={"uid": AUTHENTICATED_USER},
    ), patch.object(
        query_router.query_parser_service,
        "extract_file_filters",
        return_value=parsed_query,
    ), patch.object(query_router, "logger", router_logger):
        response = client.post(
            "/rag/query/",
            headers=VALID_AUTH_HEADER,
            json={"query": private_query},
        )

    assert response.status_code == 500
    assert response.json()["detail"] == "Unable to process the query. Please try again."
    assert secret_like_text not in str(router_logger.mock_calls)
    assert private_query not in str(router_logger.mock_calls)
