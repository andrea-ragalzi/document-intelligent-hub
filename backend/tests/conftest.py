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
    Mock OpenAI API calls for all tests.
    """
    with patch("app.services.rag_service.ChatOpenAI") as mock_chat, \
         patch("app.db.chroma_client.OpenAIEmbeddings") as mock_embeddings, \
         patch("app.services.rag_service.OpenAI") as mock_openai_client:
        
        # Mock ChatOpenAI
        mock_llm = Mock()
        mock_llm.invoke.return_value.content = "This is a mocked answer based on the document content."
        mock_chat.return_value = mock_llm
        
        # Mock OpenAIEmbeddings
        mock_embed = Mock()
        mock_embed.embed_documents.return_value = [[0.1] * 1536]
        mock_embed.embed_query.return_value = [0.1] * 1536
        mock_embeddings.return_value = mock_embed
        
        # Mock OpenAI client (for direct API calls)
        mock_client = Mock()
        mock_completion = Mock()
        mock_completion.choices = [Mock(message=Mock(content="translated query"))]
        mock_client.chat.completions.create.return_value = mock_completion
        mock_openai_client.return_value = mock_client
        
        yield {
            "chat": mock_chat,
            "embeddings": mock_embeddings,
            "openai_client": mock_openai_client
        }


@pytest.fixture(scope="module")
def client():
    """
    Create a TestClient instance for testing FastAPI endpoints.
    """
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="function")
def sample_pdf():
    """
    Create a temporary PDF file for testing uploads.
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
