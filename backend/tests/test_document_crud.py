import pytest
import uuid
from fastapi.testclient import TestClient

class TestDocumentCRUD:
    
    @pytest.fixture
    def unique_user_id(self):
        return f"test-user-{uuid.uuid4()}"

    def test_check_documents_empty(self, client, unique_user_id):
        """Test checking documents when none exist"""
        response = client.get("/rag/documents/check", params={"user_id": unique_user_id})
        assert response.status_code == 200
        data = response.json()
        assert data["has_documents"] is False
        assert data["document_count"] == 0

    def test_upload_and_list_documents(self, client, sample_pdf, unique_user_id):
        """Test uploading a document and then listing it"""
        # Upload
        with open(sample_pdf, "rb") as f:
            files = {"file": ("test_crud.pdf", f, "application/pdf")}
            data = {"user_id": unique_user_id}
            response = client.post("/rag/upload/", files=files, data=data)
            assert response.status_code == 201

        # Check status
        response = client.get("/rag/documents/check", params={"user_id": unique_user_id})
        assert response.status_code == 200
        data = response.json()
        assert data["has_documents"] is True
        assert data["document_count"] >= 1

        # List documents
        response = client.get("/rag/documents/list", params={"user_id": unique_user_id})
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] >= 1
        docs = data["documents"]
        assert any(d["filename"] == "test_crud.pdf" for d in docs)

    def test_delete_document(self, client, sample_pdf, unique_user_id):
        """Test deleting a specific document"""
        # Upload first
        with open(sample_pdf, "rb") as f:
            files = {"file": ("to_delete.pdf", f, "application/pdf")}
            data = {"user_id": unique_user_id}
            client.post("/rag/upload/", files=files, data=data)

        # Delete
        response = client.delete(
            "/rag/documents/delete", 
            params={"user_id": unique_user_id, "filename": "to_delete.pdf"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["chunks_deleted"] > 0

        # Verify it's gone
        response = client.get("/rag/documents/list", params={"user_id": unique_user_id})
        docs = response.json()["documents"]
        assert not any(d["filename"] == "to_delete.pdf" for d in docs)

    def test_delete_all_documents(self, client, sample_pdf, unique_user_id):
        """Test deleting all documents for a user"""
        # Upload a couple of files
        for name in ["doc1.pdf", "doc2.pdf"]:
            with open(sample_pdf, "rb") as f:
                files = {"file": (name, f, "application/pdf")}
                data = {"user_id": unique_user_id}
                client.post("/rag/upload/", files=files, data=data)

        # Delete all
        response = client.delete("/rag/documents/delete-all", params={"user_id": unique_user_id})
        assert response.status_code == 200
        
        # Verify empty
        response = client.get("/rag/documents/check", params={"user_id": unique_user_id})
        assert response.json()["document_count"] == 0
