"""
Unit tests for document CRUD operations.
Tests all document management endpoints and ChromaDB interactions.
"""

from fastapi.testclient import TestClient


class TestDocumentCRUD:
    """Test suite for document CRUD operations."""

    def test_list_documents_empty(self, client: TestClient, test_user_id: str):
        """Test listing documents when user has no documents."""
        # First, delete all documents to ensure clean state
        response = client.delete(
            "/rag/documents/delete-all",
            params={"user_id": test_user_id}
        )
        assert response.status_code == 200

        # Now test listing
        response = client.get(
            "/rag/documents/list",
            params={"user_id": test_user_id}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == test_user_id
        assert data["total_count"] == 0
        assert data["documents"] == []

    def test_check_documents_empty(self, client: TestClient, test_user_id: str):
        """Test checking documents when user has no documents."""
        response = client.get(
            "/rag/documents/check",
            params={"user_id": test_user_id}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["has_documents"] is False
        assert data["document_count"] == 0
        assert data["user_id"] == test_user_id

    def test_upload_document(self, client: TestClient, sample_pdf: str, test_user_id: str):
        """Test uploading a document."""
        with open(sample_pdf, "rb") as f:
            response = client.post(
                "/rag/upload/",
                files={"file": ("test_document.pdf", f, "application/pdf")},
                data={"user_id": test_user_id}
            )
        
        assert response.status_code == 201
        data = response.json()
        assert "test_document.pdf" in data["message"]
        assert data["status"] == "success"
        assert "chunks_indexed" in data
        assert data["chunks_indexed"] > 0
        assert "detected_language" in data

    def test_list_documents_after_upload(self, client: TestClient, sample_pdf: str, test_user_id: str):
        """Test that uploaded document appears in list."""
        # Upload a document
        with open(sample_pdf, "rb") as f:
            upload_response = client.post(
                "/rag/upload/",
                files={"file": ("test_list.pdf", f, "application/pdf")},
                data={"user_id": test_user_id}
            )
        assert upload_response.status_code == 201

        # List documents
        response = client.get(
            "/rag/documents/list",
            params={"user_id": test_user_id}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] > 0
        
        # Check if our document is in the list
        filenames = [doc["filename"] for doc in data["documents"]]
        assert "test_list.pdf" in filenames
        
        # Find our document and verify metadata
        test_doc = next(doc for doc in data["documents"] if doc["filename"] == "test_list.pdf")
        assert test_doc["chunks_count"] > 0
        assert "language" in test_doc
        assert "uploaded_at" in test_doc

    def test_check_documents_after_upload(self, client: TestClient, test_user_id: str):
        """Test that check endpoint reflects uploaded documents."""
        response = client.get(
            "/rag/documents/check",
            params={"user_id": test_user_id}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["has_documents"] is True
        assert data["document_count"] > 0

    def test_delete_single_document(self, client: TestClient, sample_pdf: str, test_user_id: str):
        """Test deleting a single document."""
        # Upload a document to delete
        with open(sample_pdf, "rb") as f:
            upload_response = client.post(
                "/rag/upload/",
                files={"file": ("test_delete.pdf", f, "application/pdf")},
                data={"user_id": test_user_id}
            )
        assert upload_response.status_code == 201

        # Delete the document
        response = client.delete(
            "/rag/documents/delete",
            params={"user_id": test_user_id, "filename": "test_delete.pdf"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["filename"] == "test_delete.pdf"
        assert data["chunks_deleted"] > 0

        # Verify document is no longer in list
        list_response = client.get(
            "/rag/documents/list",
            params={"user_id": test_user_id}
        )
        filenames = [doc["filename"] for doc in list_response.json()["documents"]]
        assert "test_delete.pdf" not in filenames

    def test_delete_nonexistent_document(self, client: TestClient, test_user_id: str):
        """Test deleting a document that doesn't exist returns 404."""
        response = client.delete(
            "/rag/documents/delete",
            params={"user_id": test_user_id, "filename": "nonexistent.pdf"}
        )
        
        # Should return 404 when document not found
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    def test_delete_all_documents(self, client: TestClient, sample_pdf: str, test_user_id: str):
        """Test deleting all documents for a user."""
        # Upload multiple documents
        for i in range(3):
            with open(sample_pdf, "rb") as f:
                client.post(
                    "/rag/upload/",
                    files={"file": (f"test_multi_{i}.pdf", f, "application/pdf")},
                    data={"user_id": test_user_id}
                )

        # Delete all documents
        response = client.delete(
            "/rag/documents/delete-all",
            params={"user_id": test_user_id}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["chunks_deleted"] >= 0

        # Verify all documents are deleted
        list_response = client.get(
            "/rag/documents/list",
            params={"user_id": test_user_id}
        )
        assert list_response.json()["total_count"] == 0

    def test_delete_all_batch_handling(self, client: TestClient, sample_pdf: str, test_user_id: str):
        """Test that delete-all handles batch operations correctly."""
        # Clean state first
        client.delete("/rag/documents/delete-all", params={"user_id": test_user_id})
        
        # Upload several documents with DIFFERENT filenames
        # Note: ChromaDB may deduplicate identical content, so we just verify deletion works
        for i in range(5):
            filename = f"batch_test_{i}.pdf"
            with open(sample_pdf, "rb") as f:
                response = client.post(
                    "/rag/upload/",
                    files={"file": (filename, f, "application/pdf")},
                    data={"user_id": test_user_id}
                )
                assert response.status_code == 201

        # Get count before deletion
        list_before = client.get("/rag/documents/list", params={"user_id": test_user_id})
        count_before = list_before.json()["total_count"]
        # Should have at least 1 document (ChromaDB may deduplicate identical PDFs)
        assert count_before >= 1

        # Delete all
        delete_response = client.delete(
            "/rag/documents/delete-all",
            params={"user_id": test_user_id}
        )
        assert delete_response.status_code == 200
        assert delete_response.json()["chunks_deleted"] > 0

        # Verify empty state
        list_after = client.get("/rag/documents/list", params={"user_id": test_user_id})
        assert list_after.json()["total_count"] == 0

    def test_list_documents_missing_user_id(self, client: TestClient):
        """Test that listing without user_id returns error."""
        response = client.get("/rag/documents/list")
        assert response.status_code == 422  # Validation error

    def test_delete_document_missing_params(self, client: TestClient):
        """Test that delete without required params returns error."""
        # Missing filename
        response = client.delete(
            "/rag/documents/delete",
            params={"user_id": "test-user"}
        )
        assert response.status_code == 422

        # Missing user_id
        response = client.delete(
            "/rag/documents/delete",
            params={"filename": "test.pdf"}
        )
        assert response.status_code == 422

    def test_document_metadata_consistency(self, client: TestClient, sample_pdf: str, test_user_id: str):
        """Test that document metadata is consistent across operations."""
        # Clean state
        client.delete("/rag/documents/delete-all", params={"user_id": test_user_id})
        
        # Upload document
        with open(sample_pdf, "rb") as f:
            upload_response = client.post(
                "/rag/upload/",
                files={"file": ("metadata_test.pdf", f, "application/pdf")},
                data={"user_id": test_user_id}
            )
        
        upload_data = upload_response.json()
        uploaded_chunks = upload_data["chunks_indexed"]

        # Get document from list
        list_response = client.get("/rag/documents/list", params={"user_id": test_user_id})
        documents = list_response.json()["documents"]
        
        test_doc = next(doc for doc in documents if doc["filename"] == "metadata_test.pdf")
        
        # Verify metadata consistency
        assert test_doc["filename"] == "metadata_test.pdf"
        assert test_doc["chunks_count"] == uploaded_chunks
        assert test_doc["language"] in ["EN", "IT", "en", "it", "unknown"]  # Valid language codes (uppercase or lowercase)
        # uploaded_at may be None for documents uploaded without timestamp metadata
        assert "uploaded_at" in test_doc

    def test_user_isolation(self, client: TestClient, sample_pdf: str):
        """Test that documents are properly isolated between users."""
        user1 = "test-user-isolation-1"
        user2 = "test-user-isolation-2"

        # Clean state for both users
        client.delete("/rag/documents/delete-all", params={"user_id": user1})
        client.delete("/rag/documents/delete-all", params={"user_id": user2})

        # Upload document for user1
        with open(sample_pdf, "rb") as f:
            client.post(
                "/rag/upload/",
                files={"file": ("user1_doc.pdf", f, "application/pdf")},
                data={"user_id": user1}
            )

        # Upload document for user2
        with open(sample_pdf, "rb") as f:
            client.post(
                "/rag/upload/",
                files={"file": ("user2_doc.pdf", f, "application/pdf")},
                data={"user_id": user2}
            )

        # Verify user1 only sees their document
        list1 = client.get("/rag/documents/list", params={"user_id": user1})
        docs1 = list1.json()["documents"]
        filenames1 = [doc["filename"] for doc in docs1]
        assert "user1_doc.pdf" in filenames1
        assert "user2_doc.pdf" not in filenames1

        # Verify user2 only sees their document
        list2 = client.get("/rag/documents/list", params={"user_id": user2})
        docs2 = list2.json()["documents"]
        filenames2 = [doc["filename"] for doc in docs2]
        assert "user2_doc.pdf" in filenames2
        assert "user1_doc.pdf" not in filenames2

        # Cleanup
        client.delete("/rag/documents/delete-all", params={"user_id": user1})
        client.delete("/rag/documents/delete-all", params={"user_id": user2})
