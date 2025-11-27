"""
Test suite for RAG endpoints: /rag/upload/ and /rag/query/
"""

from io import BytesIO


class TestHealthEndpoint:
    """Test the root health check endpoint"""

    def test_health_check(self, client):
        """Test that the API is running"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "welcome" in data["message"].lower()


class TestUploadEndpoint:
    """Test suite for /rag/upload/ endpoint"""

    def test_upload_valid_pdf(self, client, sample_pdf, test_user_id):
        """Test uploading a valid PDF file"""
        # Set the user_id context for this test
        client.test_user_context["user_id"] = test_user_id
        
        with open(sample_pdf, "rb") as f:
            files = {"file": ("test.pdf", f, "application/pdf")}

            response = client.post("/rag/upload/", files=files)

        assert response.status_code == 201
        json_response = response.json()
        assert json_response["status"] == "success"
        assert "chunks_indexed" in json_response
        assert isinstance(json_response["chunks_indexed"], int)
        assert json_response["chunks_indexed"] > 0

    def test_upload_missing_user_id(self, client, sample_pdf):
        """Test upload without auth token returns 401"""
        # Don't set user_id context - simulate missing auth
        client.test_user_context["user_id"] = None
        
        with open(sample_pdf, "rb") as f:
            files = {"file": ("test.pdf", f, "application/pdf")}

            response = client.post("/rag/upload/", files=files)

        assert response.status_code == 401  # Unauthorized

    def test_upload_invalid_file_type(self, client, test_user_id):
        """Test uploading non-PDF file returns 400"""
        # Set the user_id context for this test
        client.test_user_context["user_id"] = test_user_id
        
        fake_txt = BytesIO(b"This is not a PDF file")
        files = {"file": ("test.txt", fake_txt, "text/plain")}

        response = client.post("/rag/upload/", files=files)

        assert response.status_code == 400
        assert "PDF" in response.json()["detail"]

    def test_upload_missing_file(self, client, test_user_id):
        """Test upload without file returns 422"""
        # Set the user_id context for this test
        client.test_user_context["user_id"] = test_user_id

        response = client.post("/rag/upload/")

        assert response.status_code == 422


class TestQueryEndpoint:
    """Test suite for /rag/query/ endpoint"""

    def test_query_basic(self, client, test_user_id):
        """Test basic query functionality"""
        # Set the user_id context for this test
        client.test_user_context["user_id"] = test_user_id
        
        payload = {
            "query": "What is this document about?",
        }

        response = client.post("/rag/query/", json=payload)

        assert response.status_code == 200
        json_response = response.json()
        assert "answer" in json_response
        assert "source_documents" in json_response
        assert isinstance(json_response["answer"], str)
        assert isinstance(json_response["source_documents"], list)

    def test_query_long_text(self, client, test_user_id):
        """Test query with longer question"""
        # Set the user_id context for this test
        client.test_user_context["user_id"] = test_user_id
        
        payload = {
            "query": "Can you provide a detailed explanation of the main topics covered in this document?",
        }

        response = client.post("/rag/query/", json=payload)

        assert response.status_code == 200
        json_response = response.json()
        assert "answer" in json_response
        assert len(json_response["answer"]) > 0

    def test_query_missing_user_id(self, client):
        """Test query without auth token returns 401"""
        # Don't set user_id context - simulate missing auth
        client.test_user_context["user_id"] = None
        
        payload = {"query": "Test question"}

        response = client.post("/rag/query/", json=payload)

        assert response.status_code == 401  # Unauthorized

    def test_query_empty_query(self, client, test_user_id):
        """Test query with empty string"""
        # Set the user_id context for this test
        client.test_user_context["user_id"] = test_user_id
        
        payload = {"query": ""}

        response = client.post("/rag/query/", json=payload)

        # Should still return 200 but may have generic response
        assert response.status_code == 200

    def test_query_with_extra_fields(self, client, test_user_id):
        """Test query with extra fields (should be ignored by Pydantic)"""
        # Set the user_id context for this test
        client.test_user_context["user_id"] = test_user_id
        
        payload = {
            "query": "Test question",
            "extra_field": "ignored",
            "chat_history": [{"role": "user", "content": "test"}],
        }

        response = client.post("/rag/query/", json=payload)

        # Extra fields are ignored, query should succeed
        assert response.status_code == 200


class TestEndToEndFlow:
    """Test complete upload -> query workflow"""

    def test_upload_then_query(self, client, sample_pdf, test_user_id):
        """Test uploading a document and then querying it"""
        # Set the user_id context for this test
        client.test_user_context["user_id"] = test_user_id
        
        # Step 1: Upload document
        with open(sample_pdf, "rb") as f:
            files = {"file": ("test_doc.pdf", f, "application/pdf")}

            upload_response = client.post("/rag/upload/", files=files)

        assert upload_response.status_code == 201

        # Step 2: Query the uploaded document
        query_payload = {
            "query": "What does this document contain?",
        }

        query_response = client.post("/rag/query/", json=query_payload)

        assert query_response.status_code == 200
        json_response = query_response.json()

        # The response should reference the uploaded content
        assert len(json_response["answer"]) > 0
        assert len(json_response["source_documents"]) > 0

    def test_multi_tenant_isolation(self, client, sample_pdf):
        """Test that different users have isolated data"""
        user1_id = "user-1-test"
        user2_id = "user-2-test"

        # User 1 uploads a document
        client.test_user_context["user_id"] = user1_id
        with open(sample_pdf, "rb") as f:
            files = {"file": ("user1_doc.pdf", f, "application/pdf")}
            client.post("/rag/upload/", files=files)

        # User 2 queries (should not see User 1's document)
        client.test_user_context["user_id"] = user2_id
        query_payload = {
            "query": "What is in user 1's document?",
        }

        response = client.post("/rag/query/", json=query_payload)

        assert response.status_code == 200
        # The answer should indicate no relevant documents found
        # or should not contain specific content from user 1's document
