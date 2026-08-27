"""Security boundary tests for Firebase authentication and tenant isolation."""

from collections.abc import Generator
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient
from firebase_admin import auth

from app.routers import query_router
from app.schemas.rag_schema import DocumentInfo, FileFilterResponse
from app.services.rag_orchestrator_service import RAGService, get_rag_service
from main import app


AUTHENTICATED_USER = "user-a"
OTHER_USER = "user-b"
VALID_AUTH_HEADER = {"Authorization": "Bearer verified-user-a-token"}


@pytest.fixture
def protected_client() -> Generator[tuple[TestClient, Mock], None, None]:
    """Use real authentication with a fake RAG service and no app lifespan."""
    previous_overrides = app.dependency_overrides.copy()
    rag_service = Mock(spec=RAGService)

    app.dependency_overrides.clear()
    app.dependency_overrides[get_rag_service] = lambda: rag_service
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
    assert response.json()["filename"] == "alice-cheshire-cat-demo.pdf"
    assert response.json()["suggested_questions"] == [
        "What does Alice first notice about the Cheshire Cat?",
        "How is the Cheshire Cat described?",
        "What happens when the Cat disappears?",
    ]
    rag_service.user_document_exists.assert_called_once_with(
        AUTHENTICATED_USER, "alice-cheshire-cat-demo.pdf"
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


def test_query_uses_verified_uid_and_ignores_spoofed_user_id(
    protected_client: tuple[TestClient, Mock],
) -> None:
    """RAG discovery and answer generation must both receive the verified UID."""
    client, rag_service = protected_client
    rag_service.get_user_documents.return_value = [
        DocumentInfo(filename="user-a.pdf", chunks_count=1, language="EN")
    ]
    rag_service.answer_query.return_value = ("Scoped answer", ["user-a.pdf"])

    usage_service = Mock()
    usage_service.check_query_limit.return_value = (True, 0)
    usage_service.increment_user_queries.return_value = 1
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
        query_router,
        "_get_user_tier_limits",
        return_value=("FREE", 20),
    ), patch.object(
        query_router,
        "get_usage_service",
        return_value=usage_service,
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
    )
    usage_service.check_query_limit.assert_called_once_with(
        AUTHENTICATED_USER,
        20,
    )
    usage_service.increment_user_queries.assert_called_once_with(AUTHENTICATED_USER)
