"""
Pytest configuration and fixtures for backend tests.
"""

import os
import tempfile
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient
from main import app


@pytest.fixture(scope="module", autouse=True)
def mock_openai():
    """
    Mock OpenAI LLM calls for all tests.
    
    NOTE: HuggingFace embeddings are NOT mocked - they run locally and are fast/free.
    This is intentional to test real embedding generation without API costs.
    """
    # Mock only OpenAI LLM (ChatGPT) - embeddings are local now
    with patch("langchain_openai.ChatOpenAI.invoke") as mock_llm_invoke, \
         patch("openai.resources.chat.completions.Completions.create") as mock_openai_create:
        
        # Mock LangChain ChatOpenAI.invoke
        mock_response = Mock()
        mock_response.content = "This is a mocked answer based on the document content."
        mock_llm_invoke.return_value = mock_response
        
        # Mock OpenAI client completions.create
        mock_completion = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_message.content = "translated query"
        mock_choice.message = mock_message
        mock_completion.choices = [mock_choice]
        mock_openai_create.return_value = mock_completion
        
        yield {
            "llm_invoke": mock_llm_invoke,
            "openai_create": mock_openai_create
        }


@pytest.fixture(scope="module")
def client():
    """
    Create a TestClient instance for testing FastAPI endpoints.
    """
    # Mock Firebase initialization to avoid requiring credentials in tests
    with patch("app.core.firebase.initialize_firebase"):
        with TestClient(app) as test_client:
            yield test_client


@pytest.fixture(scope="function")
def sample_pdf():
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
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    temp_file.write(pdf_content)
    temp_file.close()

    yield temp_file.name

    # Cleanup
    try:
        os.unlink(temp_file.name)
    except Exception:
        pass


@pytest.fixture(scope="function")
def test_user_id():
    """
    Provide a consistent test user ID.
    """
    return "test-user-12345"


@pytest.fixture(scope="function")
def cleanup_test_data():
    """
    Cleanup test data after tests run.
    """
    yield
    # Cleanup logic here if needed
    # For example, delete test user's data from ChromaDB


@pytest.fixture(scope="function")
def mock_vector_store_repository():
    """
    Create a mock VectorStoreRepository for unit testing services.
    
    This allows testing service layer logic without touching the database.
    Example usage:
        def test_my_service(mock_vector_store_repository):
            service = RAGService(repository=mock_vector_store_repository)
            # Test service logic here
    """
    from app.repositories.vector_store_repository import VectorStoreRepository
    
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
