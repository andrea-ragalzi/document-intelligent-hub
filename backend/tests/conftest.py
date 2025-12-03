"""
Pytest configuration and fixtures for backend tests.
"""

import os

# New imports for ChromaDB cleanup
import shutil
import tempfile
from typing import Generator
from unittest.mock import Mock, patch

import pytest
from app.core.config import settings
from fastapi.testclient import TestClient
from main import app


class TestClientWithContext(TestClient):
    """
    Extended TestClient with test_user_context attribute for auth mocking.
    This allows type-safe access to the context dictionary in tests.
    """

    test_user_context: dict[str, str | None]


@pytest.fixture(scope="session", autouse=True)
def cleanup_chroma_db_after_session() -> Generator[None, None, None]:
    """
    Fixture to clean up the ChromaDB test directory after the test session.
    This runs once per session, after all tests are complete.
    """
    yield
    # Teardown: remove the test database directory
    if "test" in settings.CHROMA_DB_PATH and os.path.exists(settings.CHROMA_DB_PATH):
        print(f"🧹 Cleaning up ChromaDB test directory: {settings.CHROMA_DB_PATH}")
        shutil.rmtree(settings.CHROMA_DB_PATH)


@pytest.fixture(scope="module", autouse=True)
def mock_firebase_auth() -> Generator[dict[str, Mock], None, None]:
    """
    Mock Firebase Admin SDK auth functions to avoid real auth calls in tests.
    This prevents tests from failing due to missing credentials or network issues.
    """
    with patch("firebase_admin.auth.verify_id_token") as mock_verify_id_token, patch(
        "firebase_admin.auth.get_user"
    ) as mock_get_user:

        # Mock verify_id_token
        mock_verify_id_token.return_value = {"uid": "test-user-12345"}

        # Mock get_user
        mock_user = Mock()
        mock_user.uid = "test-user-12345"
        mock_user.email = "test@example.com"
        mock_user.custom_claims = {"tier": "FREE"}
        mock_get_user.return_value = mock_user

        yield {"verify_id_token": mock_verify_id_token, "get_user": mock_get_user}


@pytest.fixture(scope="module")
def client() -> Generator[TestClientWithContext, None, None]:
    """
    Create a TestClient instance for testing FastAPI endpoints.
    Mock Firebase auth to bypass token verification in tests.

    The mock returns a test user ID that can be overridden per-test.
    """
    from app.core.auth import (
        verify_firebase_token,
    )  # pylint: disable=import-outside-toplevel
    from fastapi import HTTPException, status  # pylint: disable=import-outside-toplevel

    # Shared state for current test user ID (can be None for auth failure tests)
    test_user_context: dict[str, str | None] = {"user_id": "test-user-12345"}

    def mock_verify_token() -> str:
        """
        Mock Firebase token verification for tests.
        Returns the current test user ID without verifying any token.
        Raises 401 if user_id is None (simulating missing auth).
        """
        user_id = test_user_context["user_id"]
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing Authorization header",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user_id

    # Mock Firebase initialization to avoid requiring credentials in tests
    with patch("app.core.firebase.initialize_firebase"):

        # Override the dependency in the app to bypass token verification
        app.dependency_overrides[verify_firebase_token] = mock_verify_token

        with TestClientWithContext(app) as test_client:
            # Attach context to client for tests to modify
            test_client.test_user_context = test_user_context
            yield test_client

        # Clean up dependency overrides after tests
        app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def sample_pdf() -> Generator[str, None, None]:
    """
    Create a temporary PDF file for testing uploads.

    NOTE: This minimal PDF may not parse correctly with UnstructuredPDFLoader
    in production environment. Upload tests (test_upload_document, etc.) may fail
    with 500 errors due to PDF parsing issues, not code logic errors.

    For real testing, use actual PDF files. The core CRUD operations
    (list, check, delete) work correctly as shown by passing tests.
    """
    # Create a minimal valid PDF
    pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/Resources <<
/Font <<
/F1 <<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
>>
>>
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(Test PDF Document) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000317 00000 n
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
410
%%EOF"""

    # Create temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        temp_file.write(pdf_content)
        temp_file_name = temp_file.name

    yield temp_file_name

    # Cleanup
    try:
        os.unlink(temp_file_name)
    except Exception:  # pylint: disable=broad-exception-caught
        pass


@pytest.fixture(scope="function")
def test_user_id() -> str:
    """
    Provide a consistent test user ID.
    """
    return "test-user-12345"


@pytest.fixture(scope="function")
def cleanup_test_data() -> Generator[None, None, None]:
    """
    Cleanup test data after tests run.
    """
    yield
    # Cleanup logic here if needed
    # For example, delete test user's data from ChromaDB


@pytest.fixture(scope="function")
def mock_vector_store_repository() -> Generator[Mock, None, None]:
    """
    Create a mock VectorStoreRepository for unit testing services.

    This allows testing service layer logic without touching the database.
    Example usage:
        def test_my_service(mock_vector_store_repository) -> None:
            service = RAGService(repository=mock_vector_store_repository)
            # Test service logic here
    """
    from app.repositories.vector_store_repository import (  # pylint: disable=import-outside-toplevel
        VectorStoreRepository,
    )

    mock_repo = Mock(spec=VectorStoreRepository)

    # Configure default behaviors
    mock_repo.add_documents.return_value = 10
    mock_repo.check_document_exists.return_value = False
    mock_repo.get_user_chunks_sample.return_value = ([], [])
    mock_repo.count_document_chunks.return_value = 0
    mock_repo.similarity_search.return_value = []
    mock_repo.delete_document.return_value = 5
    mock_repo.delete_all_user_documents.return_value = 20

    # Mock retriever
    mock_retriever = Mock()
    mock_retriever.invoke.return_value = []
    mock_repo.get_retriever.return_value = mock_retriever

    return mock_repo


@pytest.fixture(scope="function", autouse=True)
def mock_usage_service() -> Generator[Mock, None, None]:
    """
    Mock the usage tracking service to prevent hitting rate limits in tests.
    This fixture will automatically be used in all tests.
    Patches both query_router and auth_router usage service imports.
    """
    with patch(
        "app.routers.query_router.get_usage_service"
    ) as mock_get_service_query, patch(
        "app.routers.auth_router.get_usage_service"
    ) as mock_get_service_auth:
        # Create a mock for the service *instance*
        mock_service_instance = Mock()

        # check_query_limit is SYNCHRONOUS - returns tuple directly (not awaitable)
        mock_service_instance.check_query_limit = Mock(return_value=(True, 0))

        # increment_user_queries is also SYNCHRONOUS
        mock_service_instance.increment_user_queries = Mock(return_value=1)

        # get_user_queries_today is also SYNCHRONOUS
        mock_service_instance.get_user_queries_today = Mock(return_value=0)

        # The dependency-injected function `get_usage_service` should return this instance.
        mock_get_service_query.return_value = mock_service_instance
        mock_get_service_auth.return_value = mock_service_instance

        yield mock_service_instance


@pytest.fixture(scope="function", autouse=True)
def mock_email_service() -> Generator[Mock, None, None]:
    """
    Mock the email service to prevent sending real emails during tests.
    This fixture will automatically be used in all tests.
    """
    with patch(
        "app.routers.auth_router.get_email_service"
    ) as mock_get_service_auth, patch(
        "app.services.email_service.get_email_service"
    ) as mock_get_service_global:

        # Create a mock for the service *instance*
        mock_service_instance = Mock()

        # Configure default behaviors - return True (success) but do nothing
        mock_service_instance.send_bug_report.return_value = True
        mock_service_instance.send_feedback.return_value = True
        mock_service_instance.send_invitation_request.return_value = True

        # The dependency-injected function `get_email_service` should return this instance.
        mock_get_service_auth.return_value = mock_service_instance
        mock_get_service_global.return_value = mock_service_instance

        yield mock_service_instance
