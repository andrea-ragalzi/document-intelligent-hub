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
    # Mock at the lowest level - the actual API call methods
    with patch("langchain_openai.ChatOpenAI.invoke") as mock_llm_invoke, \
         patch("langchain_openai.OpenAIEmbeddings.embed_documents") as mock_embed_docs, \
         patch("langchain_openai.OpenAIEmbeddings.embed_query") as mock_embed_query, \
         patch("openai.resources.chat.completions.Completions.create") as mock_openai_create:
        
        # Mock LangChain ChatOpenAI.invoke
        mock_response = Mock()
        mock_response.content = "This is a mocked answer based on the document content."
        mock_llm_invoke.return_value = mock_response
        
        # Mock OpenAIEmbeddings methods
        mock_embed_docs.return_value = [[0.1] * 1536]
        mock_embed_query.return_value = [0.1] * 1536
        
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
            "embed_docs": mock_embed_docs,
            "embed_query": mock_embed_query,
            "openai_create": mock_openai_create
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
