"""
Integration tests for VectorStoreRepository.

These tests verify the repository layer in isolation with a real ChromaDB instance.
They test CRUD operations, metadata filtering, and multi-tenancy isolation.
"""

from typing import Any

import pytest
from app.db.chroma_client import (
    get_chroma_client,
    get_chroma_collection,
    get_vector_store,
)
from app.repositories.vector_store_repository import VectorStoreRepository
from langchain_core.documents import Document


@pytest.fixture(scope="function")
def test_repository():  # pylint: disable=W0621
    """
    Create a real VectorStoreRepository for integration testing.

    Uses real ChromaDB instance (test mode) to verify actual database operations.
    """
    # Get real dependencies
    chroma_client = get_chroma_client()
    collection = get_chroma_collection(chroma_client)

    # Get vector store (generator)
    vector_store_gen = get_vector_store()
    vector_store = next(vector_store_gen)

    # Create repository
    repository = VectorStoreRepository(
        vector_store=vector_store,
        collection=collection
    )

    yield repository

    # Cleanup: Delete all test data
    try:
        test_user_ids = ["test-repo-user-1", "test-repo-user-2", "test-repo-user-3"]
        for user_id in test_user_ids:
            try:
                collection.delete(where={"source": user_id})
            except (ValueError, KeyError, RuntimeError):
                # Ignore cleanup errors - collection might be empty or already deleted
                pass
    finally:
        # Close vector store generator
        try:
            next(vector_store_gen)
        except StopIteration:
            pass


# pylint: disable=W0621  # test_repository fixture redefines name from outer scope (pytest pattern)
class TestRepositoryBasicOperations:
    """Test basic CRUD operations"""

    def test_add_documents(self, test_repository: Any):
        """Test adding documents to vector store"""
        documents = [
            Document(
                page_content="This is the first test document.",
                metadata={
                    "source": "test-repo-user-1",
                    "original_filename": "test1.pdf",
                    "chunk_index": 0
                }
            ),
            Document(
                page_content="This is the second test document.",
                metadata={
                    "source": "test-repo-user-1",
                    "original_filename": "test1.pdf",
                    "chunk_index": 1
                }
            )
        ]

        total_indexed = test_repository.add_documents(documents, batch_size=100)

        assert total_indexed == 2

    def test_check_document_exists(self, test_repository: Any):
        """Test checking if document exists"""
        # First add a document
        documents = [
            Document(
                page_content="Test content for existence check.",
                metadata={
                    "source": "test-repo-user-1",
                    "original_filename": "exists.pdf",
                    "chunk_index": 0
                }
            )
        ]
        test_repository.add_documents(documents)

        # Check if it exists
        exists = test_repository.check_document_exists(
            user_id="test-repo-user-1",
            filename="exists.pdf"
        )
        assert exists is True

        # Check non-existent document
        not_exists = test_repository.check_document_exists(
            user_id="test-repo-user-1",
            filename="nonexistent.pdf"
        )
        assert not_exists is False

    def test_count_document_chunks(self, test_repository: Any):
        """Test counting chunks for a specific document"""
        # Add multiple chunks
        documents = [
            Document(
                page_content=f"Chunk {i} content",
                metadata={
                    "source": "test-repo-user-1",
                    "original_filename": "chunked.pdf",
                    "chunk_index": i
                }
            )
            for i in range(5)
        ]
        test_repository.add_documents(documents)

        # Count chunks
        count = test_repository.count_document_chunks(
            user_id="test-repo-user-1",
            filename="chunked.pdf"
        )

        assert count == 5

    def test_get_user_chunks_sample(self, test_repository: Any):
        """Test getting a sample of user chunks"""
        # Add documents
        documents = [
            Document(
                page_content=f"Sample chunk {i}",
                metadata={
                    "source": "test-repo-user-1",
                    "original_filename": f"doc{i}.pdf",
                    "chunk_index": 0
                }
            )
            for i in range(3)
        ]
        test_repository.add_documents(documents)

        # Get sample
        metadatas, ids = test_repository.get_user_chunks_sample(
            user_id="test-repo-user-1",
            sample_size=10
        )

        assert len(metadatas) >= 3
        assert len(ids) >= 3
        assert all(meta["source"] == "test-repo-user-1" for meta in metadatas)

    def test_similarity_search(self, test_repository: Any):
        """Test similarity search functionality"""
        # Add documents with specific content
        documents = [
            Document(
                page_content="Python is a programming language used for data science.",
                metadata={
                    "source": "test-repo-user-1",
                    "original_filename": "python.pdf",
                    "chunk_index": 0
                }
            ),
            Document(
                page_content="JavaScript is used for web development.",
                metadata={
                    "source": "test-repo-user-1",
                    "original_filename": "javascript.pdf",
                    "chunk_index": 0
                }
            )
        ]
        test_repository.add_documents(documents)

        # Search for Python-related content
        results = test_repository.similarity_search(
            query="programming language for data",
            user_id="test-repo-user-1",
            k=2
        )

        assert len(results) > 0
        # Should find the Python document as most relevant
        assert any("Python" in doc.page_content for doc in results)

    def test_delete_document(self, test_repository: Any):
        """Test deleting a specific document"""
        # Add document
        documents = [
            Document(
                page_content="Content to be deleted",
                metadata={
                    "source": "test-repo-user-1",
                    "original_filename": "delete_me.pdf",
                    "chunk_index": 0
                }
            )
        ]
        test_repository.add_documents(documents)

        # Verify it exists
        assert test_repository.check_document_exists("test-repo-user-1", "delete_me.pdf")

        # Delete it
        deleted_count = test_repository.delete_document(
            user_id="test-repo-user-1",
            filename="delete_me.pdf"
        )

        assert deleted_count >= 1

        # Verify it's gone
        assert not test_repository.check_document_exists("test-repo-user-1", "delete_me.pdf")

    def test_delete_all_user_documents(self, test_repository: Any):
        """Test deleting all documents for a user"""
        # Add multiple documents
        documents = [
            Document(
                page_content=f"User document {i}",
                metadata={
                    "source": "test-repo-user-2",
                    "original_filename": f"doc{i}.pdf",
                    "chunk_index": 0
                }
            )
            for i in range(3)
        ]
        test_repository.add_documents(documents)

        # Delete all user documents
        deleted_count = test_repository.delete_all_user_documents("test-repo-user-2")

        assert deleted_count >= 3

        # Verify all are gone
        metadatas, _ = test_repository.get_user_chunks_sample("test-repo-user-2")
        assert len(metadatas) == 0


# pylint: disable=W0621  # test_repository fixture redefines name from outer scope (pytest pattern)
class TestMultiTenancyIsolation:
    """Test that users can only access their own data"""

    def test_user_isolation_in_similarity_search(self, test_repository: Any):
        """Test that similarity search respects user_id filtering"""
        # Add documents for User 1
        user1_docs = [
            Document(
                page_content="User 1 secret information about Project Alpha.",
                metadata={
                    "source": "test-repo-user-1",
                    "original_filename": "user1_secret.pdf",
                    "chunk_index": 0
                }
            )
        ]
        test_repository.add_documents(user1_docs)

        # Add documents for User 2
        user2_docs = [
            Document(
                page_content="User 2 information about Project Beta.",
                metadata={
                    "source": "test-repo-user-2",
                    "original_filename": "user2_info.pdf",
                    "chunk_index": 0
                }
            )
        ]
        test_repository.add_documents(user2_docs)

        # User 2 searches for "Alpha" (User 1's content)
        results = test_repository.similarity_search(
            query="Project Alpha",
            user_id="test-repo-user-2",  # User 2's ID
            k=10
        )

        # Should NOT return User 1's documents
        for doc in results:
            assert doc.metadata["source"] == "test-repo-user-2"
            assert "Alpha" not in doc.page_content

    def test_user_isolation_in_chunk_sample(self, test_repository: Any):
        """Test that chunk samples are user-specific"""
        # Add documents for multiple users
        for user_id in ["test-repo-user-1", "test-repo-user-2"]:
            docs = [
                Document(
                    page_content=f"Content for {user_id}",
                    metadata={
                        "source": user_id,
                        "original_filename": f"{user_id}_doc.pdf",
                        "chunk_index": 0
                    }
                )
            ]
            test_repository.add_documents(docs)

        # Get chunks for User 1 only
        metadatas, _ = test_repository.get_user_chunks_sample("test-repo-user-1")

        # Should only contain User 1's data
        assert all(meta["source"] == "test-repo-user-1" for meta in metadatas)

    def test_user_isolation_in_delete(self, test_repository: Any):
        """Test that delete operations respect user boundaries"""
        # Add same-named document for two users
        for user_id in ["test-repo-user-1", "test-repo-user-2"]:
            docs = [
                Document(
                    page_content=f"Content for {user_id}",
                    metadata={
                        "source": user_id,
                        "original_filename": "shared_name.pdf",
                        "chunk_index": 0
                    }
                )
            ]
            test_repository.add_documents(docs)

        # Delete User 1's document
        test_repository.delete_document("test-repo-user-1", "shared_name.pdf")

        # Verify User 1's is gone but User 2's remains
        assert not test_repository.check_document_exists("test-repo-user-1", "shared_name.pdf")
        assert test_repository.check_document_exists("test-repo-user-2", "shared_name.pdf")


# pylint: disable=W0621  # test_repository fixture redefines name from outer scope (pytest pattern)
class TestRepositoryEdgeCases:
    """Test edge cases and error handling"""

    def test_add_empty_document_list(self, test_repository: Any):
        """Test adding empty list of documents"""
        total_indexed = test_repository.add_documents([])
        assert total_indexed == 0

    def test_search_with_no_documents(self, test_repository: Any):
        """Test similarity search when user has no documents"""
        results = test_repository.similarity_search(
            query="anything",
            user_id="nonexistent-user-999",
            k=10
        )
        assert results == []

    def test_delete_nonexistent_document(self, test_repository: Any):
        """Test deleting a document that doesn't exist"""
        deleted_count = test_repository.delete_document(
            user_id="test-repo-user-3",
            filename="nonexistent.pdf"
        )
        # Should return 0 (no documents deleted)
        assert deleted_count == 0

    def test_large_batch_size(self, test_repository: Any):
        """Test adding documents with large batch size"""
        documents = [
            Document(
                page_content=f"Document {i}",
                metadata={
                    "source": "test-repo-user-1",
                    "original_filename": "batch.pdf",
                    "chunk_index": i
                }
            )
            for i in range(10)
        ]

        # Use batch size larger than document count
        total_indexed = test_repository.add_documents(documents, batch_size=1000)
        assert total_indexed == 10

    def test_retriever_factory(self, test_repository: Any):
        """Test get_retriever() returns valid LangChain retriever"""
        retriever = test_repository.get_retriever(
            user_id="test-repo-user-1",
            k=5
        )

        # Should be callable
        assert retriever is not None
        assert hasattr(retriever, "invoke") or hasattr(retriever, "get_relevant_documents")
