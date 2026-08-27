"""
Unit tests for RAGService using mock repository.

These tests verify the business logic layer in isolation WITHOUT touching
the real database. They use mock repositories to test service logic only.

This is the key benefit of the Repository Pattern - services can be tested
independently with fast, reliable mock objects.
"""

import inspect
from typing import Any
from unittest.mock import Mock, patch

import pytest
from langchain_core.documents import Document

import app.services.rag_orchestrator_service
from app.repositories.vector_store_repository import VectorStoreRepository
from app.schemas.rag_schema import ConversationMessage
from app.services.rag_orchestrator_service import RAGService


@pytest.fixture
def mock_repository() -> Mock:  # pylint: disable=W0621
    """
    Create a mock VectorStoreRepository for unit testing.

    This mock allows testing RAGService business logic without a real database.
    """
    mock_repo = Mock(spec=VectorStoreRepository)

    # Configure default mock behaviors
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


@pytest.fixture
def rag_service(mock_repository: Any) -> Any:  # pylint: disable=W0621
    """
    Create a RAGService instance with mock repository injected.

    This demonstrates the power of dependency injection - we can test
    the service layer without any database setup.
    """
    return RAGService(repository=mock_repository)


# pylint: disable=W0621  # Fixtures redefine names from outer scope (pytest pattern)
class TestRAGServiceInitialization:
    """Test RAGService initialization and dependency injection"""

    def test_service_accepts_repository(self, mock_repository: Any) -> None:
        """Test that RAGService can be initialized with repository"""
        service = RAGService(repository=mock_repository)

        assert service.repository == mock_repository
        assert service.llm is not None
        assert service.language_service is not None

    def test_service_requires_repository(self) -> None:
        """Test that RAGService requires repository parameter"""
        with pytest.raises(TypeError):
            # Should fail because repository is required
            RAGService()  # type: ignore  # pylint: disable=no-value-for-parameter


# pylint: disable=W0621  # Fixtures redefine names from outer scope (pytest pattern)
class TestQueryProcessing:
    """Test existing non-happy-path query behavior without external calls."""

    def test_answer_query_with_conversation_history(self, rag_service: Any) -> None:
        """Conversation history is preserved across orchestrator delegation."""
        conversation_history = [
            ConversationMessage(role="user", content="Previous question"),
            ConversationMessage(role="assistant", content="Previous answer"),
        ]
        rag_service.query_processing_service.reformulate_query = Mock(
            return_value="Reformulated follow-up question"
        )
        rag_service.query_processing_service.classify_query = Mock(
            return_value="GENERAL_SEARCH"
        )
        rag_service.answer_generation_service.generate_answer = Mock(
            return_value=("History-aware answer", ["history.pdf"])
        )

        answer, sources = rag_service.answer_query(
            query="Follow-up question",
            user_id="test-user",
            conversation_history=conversation_history,
        )

        assert answer == "History-aware answer"
        assert sources == ["history.pdf"]
        rag_service.answer_generation_service.generate_answer.assert_called_once_with(
            query="Reformulated follow-up question",
            user_id="test-user",
            conversation_history=conversation_history,
            output_language=None,
            include_files=None,
            exclude_files=None,
        )

    def test_answer_query_no_relevant_documents(
        self, rag_service: Any, mock_repository: Any
    ) -> None:
        """No retrieved chunks returns the existing grounded fallback without an LLM."""
        retriever = Mock()
        retriever.invoke.return_value = []
        mock_repository.get_retriever.return_value = retriever
        answer_service = rag_service.answer_generation_service
        answer_service.language_service = Mock()
        answer_service.language_service.detect_language.return_value = "EN"
        answer_service.language_service.translate_answer_back.side_effect = (
            lambda answer, _language: answer
        )
        answer_service.query_expansion_service = Mock()
        answer_service.query_expansion_service.generate_alternative_queries.return_value = (
            []
        )
        answer_service.llm = Mock()

        answer, sources = answer_service.generate_answer(
            query="Nonexistent topic",
            user_id="test-user",
        )

        assert answer == "I cannot answer this question based on the documents provided."
        assert sources == []
        answer_service.llm.invoke.assert_not_called()


# pylint: disable=W0621  # Fixtures redefine names from outer scope (pytest pattern)
class TestDocumentManagement:
    """Test document listing and deletion"""

    def test_get_user_documents(self, rag_service: Any, mock_repository: Any) -> None:
        """Test getting list of user documents"""
        # Mock repository response
        mock_metadatas = [
            {"source": "test-user", "original_filename": "doc1.pdf", "chunk_index": 0},
            {"source": "test-user", "original_filename": "doc1.pdf", "chunk_index": 1},
            {"source": "test-user", "original_filename": "doc2.pdf", "chunk_index": 0},
        ]
        mock_ids = ["id1", "id2", "id3"]
        mock_repository.get_user_chunks_sample.return_value = (mock_metadatas, mock_ids)
        mock_repository.count_document_chunks.side_effect = [
            2,
            1,
        ]  # doc1 has 2, doc2 has 1

        # Get documents
        documents = rag_service.get_user_documents(user_id="test-user")

        # Verify business logic grouped chunks by filename
        assert len(documents) == 2  # Two unique documents

        # Verify repository was called
        mock_repository.get_user_chunks_sample.assert_called_once()

    def test_get_user_documents_empty(
        self, rag_service: Any, mock_repository: Any
    ) -> None:
        """Test getting documents when user has none"""
        mock_repository.get_user_chunks_sample.return_value = ([], [])

        documents = rag_service.get_user_documents(user_id="empty-user")

        assert documents == []

    def test_delete_user_document(self, rag_service: Any, mock_repository: Any) -> None:
        """Test deleting a specific user document"""
        mock_repository.delete_document.return_value = 5

        result = rag_service.delete_user_document(
            user_id="test-user", filename="delete_me.pdf"
        )

        # Verify repository was called (positional args)
        mock_repository.delete_document.assert_called_once_with(
            "test-user", "delete_me.pdf"
        )

        # Verify business logic returns result
        assert result == 5

    def test_delete_all_user_documents(
        self, rag_service: Any, mock_repository: Any
    ) -> None:
        """Test deleting all documents for a user"""
        mock_repository.delete_all_user_documents.return_value = 15

        result = rag_service.delete_all_user_documents(user_id="test-user")

        # Verify repository was called
        mock_repository.delete_all_user_documents.assert_called_once_with("test-user")

        # Verify result (returns count, not dict)
        assert result == 15


# pylint: disable=W0621  # Fixtures redefine names from outer scope (pytest pattern)
class TestDocumentCount:
    """Test document counting functionality"""

    def test_get_user_document_count(
        self, rag_service: Any, mock_repository: Any
    ) -> None:
        """Test counting user's documents"""
        # Mock repository response
        mock_metadatas = [
            {"original_filename": "doc1.pdf"},
            {"original_filename": "doc1.pdf"},
            {"original_filename": "doc2.pdf"},
            {"original_filename": "doc3.pdf"},
        ]
        mock_repository.get_user_chunks_sample.return_value = (mock_metadatas, [])

        count = rag_service.get_user_document_count(user_id="test-user")

        # Should count unique documents (3 in this case)
        assert count == 3

    def test_get_user_document_count_zero(
        self, rag_service: Any, mock_repository: Any
    ) -> None:
        """Test counting when user has no documents"""
        mock_repository.get_user_chunks_sample.return_value = ([], [])

        count = rag_service.get_user_document_count(user_id="empty-user")

        assert count == 0


# pylint: disable=W0621  # Fixtures redefine names from outer scope (pytest pattern)
class TestServiceIsolation:
    """Test that RAGService is properly isolated from database implementation"""

    def test_service_has_no_direct_database_references(self) -> None:
        """Verify RAGService doesn't import ChromaDB directly"""
        source = inspect.getsource(app.services.rag_orchestrator_service)

        # Should NOT have direct ChromaDB imports
        assert "from chromadb import" not in source
        assert "import chromadb" not in source

        # Should have repository import
        assert "VectorStoreRepository" in source

    def test_service_only_calls_repository_methods(self, mock_repository: Any) -> None:
        """Verify service only interacts through repository interface"""
        # After any operation, service should only have called repository methods
        # This test documents the expected interface

        expected_methods = [
            "add_documents",
            "check_document_exists",
            "get_user_chunks_sample",
            "count_document_chunks",
            "similarity_search",
            "get_retriever",
            "delete_document",
            "delete_all_user_documents",
        ]

        # Verify mock repository has all expected methods
        for method in expected_methods:
            assert hasattr(mock_repository, method)


# pylint: disable=W0621  # Fixtures redefine names from outer scope (pytest pattern)
class TestEdgeCases:
    """Test edge cases and error conditions"""

    def test_query_with_empty_string(
        self, rag_service: Any, mock_repository: Any
    ) -> None:
        """Test query with empty string"""
        mock_retriever = Mock()
        mock_retriever.invoke.return_value = []
        mock_repository.get_retriever.return_value = mock_retriever

        rag_service.query_processing_service.reformulate_query = Mock(return_value="")
        rag_service.query_processing_service.classify_query = Mock(
            return_value="general"
        )
        rag_service.answer_generation_service.generate_answer = Mock(
            return_value=("No question provided", [])
        )

        # Should handle gracefully
        answer, _ = rag_service.answer_query(query="", user_id="test-user")

        assert isinstance(answer, str)

    def test_operations_with_special_characters_in_filename(
        self, mock_repository: Any
    ) -> None:
        """Test handling filenames with special characters"""
        special_filename = "document (1) [copy].pdf"

        mock_repository.check_document_exists.return_value = True

        # Should handle special characters correctly
        exists = mock_repository.check_document_exists(
            user_id="test-user", filename=special_filename
        )

        assert exists is True
        mock_repository.check_document_exists.assert_called_with(
            user_id="test-user", filename=special_filename
        )


# pylint: disable=W0621  # Fixtures redefine names from outer scope (pytest pattern)
class TestMockingBestPractices:
    """Examples of proper mocking patterns for future test development"""

    def test_example_verify_method_called_with_args(
        self, rag_service: Any, mock_repository: Any
    ) -> Any:
        """Example: Verify specific method calls with arguments"""
        mock_repository.delete_document.return_value = 1

        rag_service.delete_user_document("user123", "file.pdf")

        # Verify exact call (positional args)
        mock_repository.delete_document.assert_called_once_with("user123", "file.pdf")

    def test_example_count_method_calls(
        self, rag_service: Any, mock_repository: Any
    ) -> None:
        """Example: Count how many times a method was called"""
        mock_repository.get_user_chunks_sample.return_value = ([], [])

        # Call multiple times
        rag_service.get_user_documents("user1")
        rag_service.get_user_documents("user2")

        # Verify called twice
        assert mock_repository.get_user_chunks_sample.call_count == 2
