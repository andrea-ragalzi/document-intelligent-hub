"""Focused tests for the idempotent account-data cleanup coordinator."""

from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from app.core.auth import require_verified_email
from app.dependencies import get_document_file_storage, get_rag_service
from app.routers.documents_router import _delete_user_firestore_data
from app.services.rag_orchestrator_service import RAGService
from main import app


def test_firestore_account_cleanup_deletes_conversations_and_usage_record() -> None:
    db = Mock()
    first = Mock()
    second = Mock()
    db.collection.return_value.where.return_value.stream.return_value = [first, second]

    deleted = _delete_user_firestore_data("account-owner", db)

    assert deleted == 2
    batch = db.batch.return_value
    batch.delete.assert_any_call(first.reference)
    batch.delete.assert_any_call(second.reference)
    batch.delete.assert_any_call(db.collection.return_value.document.return_value)
    batch.commit.assert_called_once()


def test_account_cleanup_is_idempotent_when_no_resources_remain() -> None:
    db = Mock()
    db.collection.return_value.where.return_value.stream.return_value = []

    assert _delete_user_firestore_data("account-owner", db) == 0
    db.batch.return_value.delete.assert_called_once_with(
        db.collection.return_value.document.return_value
    )


def test_account_endpoint_deletes_every_owned_resource_before_returning() -> None:
    previous_overrides = app.dependency_overrides.copy()
    rag_service = Mock(spec=RAGService)
    rag_service.delete_all_user_documents.return_value = 4
    document_storage = Mock()
    db = Mock()
    db.collection.return_value.where.return_value.stream.return_value = []
    app.dependency_overrides[require_verified_email] = lambda: "test-user-12345"
    app.dependency_overrides[get_rag_service] = lambda: rag_service
    app.dependency_overrides[get_document_file_storage] = lambda: document_storage

    client = TestClient(app)
    try:
        with patch("app.routers.documents_router.firestore.client", return_value=db):
            response = client.delete("/rag/account/data")
    finally:
        client.close()
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous_overrides)

    assert response.status_code == 200
    assert response.json() == {
        "message": "Account data deleted successfully.",
        "chunks_deleted": 4,
        "conversations_deleted": 0,
    }
    rag_service.delete_all_user_documents.assert_called_once_with("test-user-12345")
    document_storage.delete_all.assert_called_once_with("test-user-12345")


def test_account_endpoint_does_not_report_success_when_vector_cleanup_fails() -> None:
    previous_overrides = app.dependency_overrides.copy()
    rag_service = Mock(spec=RAGService)
    rag_service.delete_all_user_documents.side_effect = RuntimeError("vector unavailable")
    document_storage = Mock()
    app.dependency_overrides[require_verified_email] = lambda: "test-user-12345"
    app.dependency_overrides[get_rag_service] = lambda: rag_service
    app.dependency_overrides[get_document_file_storage] = lambda: document_storage

    client = TestClient(app)
    try:
        response = client.delete("/rag/account/data")
    finally:
        client.close()
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous_overrides)

    assert response.status_code == 500
    assert response.json()["detail"] == "Unable to delete account data. Please try again."
    document_storage.delete_all.assert_not_called()
