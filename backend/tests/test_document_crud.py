"""
Integration tests for Document CRUD operations.

Tests document upload, listing, checking, and deletion endpoints.
"""

import uuid
from typing import Any

import pytest


class TestDocumentCRUD:
    """Test suite for document CRUD operations via RAG endpoints"""

    @pytest.fixture
    def unique_user_id(self):
        """Generate a unique user ID for test isolation"""
        return f"test-user-{uuid.uuid4()}"

    def test_check_documents_empty(self, client: Any, unique_user_id: str):
        """Test checking documents when none exist"""
        # Set the user_id context for this test
        client.test_user_context["user_id"] = unique_user_id

        response = client.get("/rag/documents/check")
        assert response.status_code == 200
        data = response.json()
        assert data["has_documents"] is False
        assert data["document_count"] == 0

    def test_upload_and_list_documents(
        self, client: Any, sample_pdf: Any, unique_user_id: str
    ):
        """Test uploading a document and then listing it"""
        # Set the user_id context for this test
        client.test_user_context["user_id"] = unique_user_id

        # Upload
        with open(sample_pdf, "rb") as f:
            files = {"file": ("test_crud.pdf", f, "application/pdf")}
            response = client.post("/rag/upload/", files=files)
            assert response.status_code == 201

        # Check status
        response = client.get("/rag/documents/check")
        assert response.status_code == 200
        data = response.json()
        assert data["has_documents"] is True
        assert data["document_count"] >= 1

        # List documents
        response = client.get("/rag/documents/list")
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] >= 1
        docs = data["documents"]
        assert any(d["filename"] == "test_crud.pdf" for d in docs)

    def test_delete_document(self, client: Any, sample_pdf: Any, unique_user_id: str):
        """Test deleting a specific document"""
        # Set the user_id context for this test
        client.test_user_context["user_id"] = unique_user_id

        # Upload first
        with open(sample_pdf, "rb") as f:
            files = {"file": ("to_delete.pdf", f, "application/pdf")}
            client.post("/rag/upload/", files=files)

        # Delete
        response = client.delete(
            "/rag/documents/delete", params={"filename": "to_delete.pdf"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["chunks_deleted"] > 0

        # Verify it's gone
        response = client.get("/rag/documents/list")
        docs = response.json()["documents"]
        assert not any(d["filename"] == "to_delete.pdf" for d in docs)

    def test_delete_all_documents(
        self, client: Any, sample_pdf: Any, unique_user_id: str
    ):
        """Test deleting all documents for a user"""
        # Set the user_id context for this test
        client.test_user_context["user_id"] = unique_user_id

        # Upload a couple of files
        for name in ["doc1.pdf", "doc2.pdf"]:
            with open(sample_pdf, "rb") as f:
                files = {"file": (name, f, "application/pdf")}
                client.post("/rag/upload/", files=files)

        # Delete all
        response = client.delete("/rag/documents/delete-all")
        assert response.status_code == 200

        # Verify empty
        response = client.get("/rag/documents/check")
        assert response.json()["document_count"] == 0
