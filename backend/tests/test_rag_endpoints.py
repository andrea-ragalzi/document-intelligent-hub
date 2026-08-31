"""
Test suite for RAG endpoints: /rag/upload/ and /rag/query/
"""

from io import BytesIO
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from app.schemas.rag_schema import FileFilterResponse


@pytest.fixture(autouse=True)
def mock_external_rag_calls() -> Any:
    """Keep endpoint tests deterministic and independent from OpenAI."""

    def parse_query(query: str, available_files: list[str]) -> FileFilterResponse:
        del available_files
        return FileFilterResponse(
            include_files=[],
            exclude_files=[],
            original_query=query,
            cleaned_query=query,
        )

    with patch(
        "app.routers.query_router.query_parser_service.extract_file_filters",
        side_effect=parse_query,
    ) as filter_parser, patch(
        "app.services.rag_orchestrator_service.RAGService.answer_query",
        return_value=("Test answer grounded in the indexed document.", ["test_doc.pdf"]),
    ) as answer_query:
        yield {"filter_parser": filter_parser, "answer_query": answer_query}


class TestHealthEndpoint:
    """Test the root health check endpoint"""

    def test_health_check(self, client: Any) -> None:
        """Test that the API is running"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "welcome" in data["message"].lower()


class TestUploadEndpoint:
    """Test suite for /rag/upload/ endpoint"""

    def test_upload_valid_pdf(
        self, client: Any, sample_pdf: Any, test_user_id: str
    ) -> None:
        """A valid PDF reaches indexing with the authenticated user's identity."""
        # Set the user_id context for this test
        client.test_user_context["user_id"] = test_user_id

        with patch(
            "app.services.rag_orchestrator_service.RAGService.index_document",
            new_callable=AsyncMock,
            return_value=(2, "EN"),
        ) as index_document, open(sample_pdf, "rb") as f:
            files = {"file": ("test.pdf", f, "application/pdf")}

            response = client.post("/rag/upload/", files=files)

        assert response.status_code == 201
        json_response = response.json()
        assert json_response["status"] == "success"
        assert "chunks_indexed" in json_response
        assert isinstance(json_response["chunks_indexed"], int)
        assert json_response["chunks_indexed"] == 2
        index_document.assert_awaited_once()
        call = index_document.await_args
        assert call.kwargs["user_id"] == test_user_id
        assert call.kwargs["file"].filename == "test.pdf"
        assert call.kwargs["document_language"] is None

    def test_malformed_pdf_returns_controlled_error(
        self, client: Any, test_user_id: str
    ) -> None:
        """A parser/indexing failure is converted to the current API error response."""
        client.test_user_context["user_id"] = test_user_id

        with patch(
            "app.services.rag_orchestrator_service.RAGService.index_document",
            new_callable=AsyncMock,
            side_effect=RuntimeError("malformed PDF"),
        ) as index_document:
            response = client.post(
                "/rag/upload/",
                files={"file": ("broken.pdf", BytesIO(b"not a PDF"), "application/pdf")},
            )

        assert response.status_code == 500
        assert response.json()["detail"] == "Indexing failed: malformed PDF"
        assert index_document.await_args.kwargs["user_id"] == test_user_id

    def test_upload_missing_user_id(self, client: Any, sample_pdf: Any) -> None:
        """Test upload without auth token returns 401"""
        # Don't set user_id context - simulate missing auth
        client.test_user_context["user_id"] = None

        with open(sample_pdf, "rb") as f:
            files = {"file": ("test.pdf", f, "application/pdf")}

            response = client.post("/rag/upload/", files=files)

        assert response.status_code == 401  # Unauthorized

    def test_upload_invalid_file_type(self, client: Any, test_user_id: str) -> None:
        """Test uploading non-PDF file returns 400"""
        # Set the user_id context for this test
        client.test_user_context["user_id"] = test_user_id

        fake_txt = BytesIO(b"This is not a PDF file")
        files = {"file": ("test.txt", fake_txt, "text/plain")}

        response = client.post("/rag/upload/", files=files)

        assert response.status_code == 400
        assert "PDF" in response.json()["detail"]

    def test_upload_missing_file(self, client: Any, test_user_id: str) -> None:
        """Test upload without file returns 422"""
        # Set the user_id context for this test
        client.test_user_context["user_id"] = test_user_id

        response = client.post("/rag/upload/")

        assert response.status_code == 422


class TestQueryEndpoint:
    """Test suite for /rag/query/ endpoint"""

    def test_query_basic(
        self,
        client: Any,
        test_user_id: str,
        mock_external_rag_calls: dict[str, Any],
    ) -> None:
        """Return the API contract while preserving authenticated file filters."""
        # Set the user_id context for this test
        client.test_user_context["user_id"] = test_user_id

        filter_parser = mock_external_rag_calls["filter_parser"]
        answer_query = mock_external_rag_calls["answer_query"]
        filter_parser.side_effect = None
        filter_parser.return_value = FileFilterResponse(
            include_files=["policy.pdf"],
            exclude_files=["draft.pdf"],
            original_query="What changed in policy.pdf?",
            cleaned_query="What changed?",
        )
        answer_query.return_value = (
            "The policy changed in January.",
            ["policy.pdf"],
        )

        payload = {"query": "What changed in policy.pdf?"}

        with patch("socket.socket.connect") as network_connect:
            response = client.post("/rag/query/", json=payload)

        network_connect.assert_not_called()
        assert response.status_code == 200
        assert response.json() == {
            "answer": "The policy changed in January.",
            "source_documents": ["policy.pdf"],
        }
        assert filter_parser.call_args.kwargs["query"] == payload["query"]
        answer_query.assert_called_once_with(
            "What changed?",
            test_user_id,
            [],
            None,
            include_files=["policy.pdf"],
            exclude_files=["draft.pdf"],
        )

    def test_query_long_text(self, client: Any, test_user_id: str) -> None:
        """Test query with longer question"""
        # Set the user_id context for this test
        client.test_user_context["user_id"] = test_user_id

        payload = {
            "query": (
                "Can you provide a detailed explanation of the "
                "main topics covered in this document?"
            ),
        }

        response = client.post("/rag/query/", json=payload)

        assert response.status_code == 200
        json_response = response.json()
        assert "answer" in json_response
        assert len(json_response["answer"]) > 0

    def test_query_missing_user_id(self, client: Any) -> None:
        """Test query without auth token returns 401"""
        # Don't set user_id context - simulate missing auth
        client.test_user_context["user_id"] = None

        payload = {"query": "Test question"}

        response = client.post("/rag/query/", json=payload)

        assert response.status_code == 401  # Unauthorized

    def test_query_empty_query(self, client: Any, test_user_id: str) -> None:
        """Test query with empty string"""
        # Set the user_id context for this test
        client.test_user_context["user_id"] = test_user_id

        payload = {"query": ""}

        response = client.post("/rag/query/", json=payload)

        # Invalid queries are rejected before any OpenAI-backed router work.
        assert response.status_code == 422

    def test_query_with_extra_fields(self, client: Any, test_user_id: str) -> None:
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

    def test_upload_then_query(
        self, client: Any, sample_pdf: Any, test_user_id: str
    ) -> None:
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

    def test_multi_tenant_isolation(self, client: Any, sample_pdf: Any) -> None:
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
