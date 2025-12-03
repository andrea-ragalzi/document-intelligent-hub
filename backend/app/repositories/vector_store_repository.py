"""
Vector Store Repository - Data Access Layer for ChromaDB

This repository encapsulates ALL ChromaDB operations, providing a clean
interface for the service layer without exposing database implementation details.

CRITICAL: All collection.get(), collection.add(), collection.delete(),
collection.query() calls MUST be in this file only.

Architecture Pattern: Repository Pattern
- Services call abstract methods like get_user_documents()
- Implementation details hidden from business logic
- Easy to swap ChromaDB with another vector store
- Testable: can be mocked without real database
"""

from typing import Any, Dict, List, Optional, Tuple

from chromadb import Collection
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStoreRetriever

from app.core.logging import logger


class VectorStoreRepository:
    """
    Repository for vector store operations (ChromaDB).

    Encapsulates all direct database access, providing a clean interface
    for the service layer.

    Constructor Injection Pattern:
    - Receives dependencies via __init__
    - No global state or singletons
    - Easy to test with mocks
    """

    def __init__(self, vector_store: Chroma, collection: Collection) -> None:
        """
        Initialize repository with injected dependencies.

        Args:
            vector_store: LangChain Chroma wrapper (for high-level operations)
            collection: Direct ChromaDB collection (for low-level operations)
        """
        self.vector_store = vector_store
        self.collection = collection
        logger.debug("✅ VectorStoreRepository initialized with injected dependencies")

    # --- CREATE Operations ---

    def add_documents(self, documents: List[Document], batch_size: int = 2000) -> int:
        """
        Add documents to the vector store with batching.

        Args:
            documents: List of LangChain Documents with content and metadata
            batch_size: Number of documents to process per batch

        Returns:
            Total number of documents indexed

        Raises:
            Exception: If indexing fails
        """
        try:
            total_indexed = 0

            for i in range(0, len(documents), batch_size):
                batch = documents[i : i + batch_size]
                self.vector_store.add_documents(batch)
                total_indexed += len(batch)
                logger.info(
                    f"📦 Batch {i // batch_size + 1}: Indexed {len(batch)} chunks "
                    f"(total: {total_indexed})"
                )

            logger.info(f"✅ Successfully indexed {total_indexed} document chunks")
            return total_indexed

        except Exception as e:
            logger.error(f"❌ Failed to add documents to vector store: {e}")
            raise

    # --- READ Operations ---

    def check_document_exists(self, user_id: str, filename: str) -> bool:
        """
        Check if a specific document already exists for a user.

        Args:
            user_id: The user ID (tenant identifier)
            filename: The filename to check

        Returns:
            True if document exists, False otherwise
        """
        try:
            results = self.collection.get(
                where={"$and": [{"source": user_id}, {"original_filename": filename}]},
                limit=1,
            )
            exists = len(results.get("ids", [])) > 0
            logger.debug(
                f"📄 Document '{filename}' exists for user {user_id}: {exists}"
            )
            return exists
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error(f"❌ Error checking document existence: {e}")
            return False

    def get_user_chunks_sample(
        self, user_id: str, sample_size: int = 10000
    ) -> Tuple[List[Any], List[str]]:
        """
        Get a sample of document chunks for a user.

        Used for discovering unique documents without loading all data.

        CRITICAL: Increased default sample_size to 10000 to ensure all documents
        are discovered even when users have multiple large PDFs.

        Args:
            user_id: The user ID
            sample_size: Number of chunks to sample (default: 10000)

        Returns:
            Tuple of (metadatas, ids)
        """
        try:
            results = self.collection.get(where={"source": user_id}, limit=sample_size)
            metadatas = results.get("metadatas", []) or []
            ids = results.get("ids", []) or []
            logger.debug(
                f"📊 Retrieved {len(metadatas)} chunk metadata samples for user {user_id}"
            )
            return metadatas, ids
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error(f"❌ Error getting user chunks sample: {e}")
            return [], []

    def count_document_chunks(self, user_id: str, filename: str) -> int:
        """
        Count the number of chunks for a specific document.

        Args:
            user_id: The user ID
            filename: The filename

        Returns:
            Number of chunks for this document
        """
        try:
            results = self.collection.get(
                where={"$and": [{"source": user_id}, {"original_filename": filename}]},
                limit=100000,
            )
            count = len(results.get("ids", []))
            logger.debug(f"📊 Document '{filename}' has {count} chunks")
            return count
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error(f"❌ Error counting document chunks: {e}")
            return 0

    def similarity_search(
        self, query: str, user_id: str, k: int = 10
    ) -> List[Document]:
        """
        Perform similarity search for a query.

        Args:
            query: The search query
            user_id: The user ID (for multi-tenancy filtering)
            k: Number of results to return

        Returns:
            List of relevant documents
        """
        try:
            # Use LangChain's similarity_search with metadata filtering
            results = self.vector_store.similarity_search(
                query=query, k=k, filter={"source": user_id}
            )
            logger.debug(f"🔍 Similarity search returned {len(results)} results")
            return results
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error(f"❌ Similarity search failed: {e}")
            return []

    def get_retriever(
        self,
        user_id: str,
        k: int = 10,
        include_files: Optional[List[str]] = None,
        exclude_files: Optional[List[str]] = None,
    ) -> VectorStoreRetriever:
        """
        Get a LangChain retriever configured for a specific user with optional file filtering.

        Args:
            user_id: The user ID (for multi-tenancy filtering)
            k: Number of results to return
            include_files: Optional list of filenames to restrict search to
                          (if provided, ONLY these files)
            exclude_files: Optional list of filenames to exclude from search

        Returns:
            LangChain retriever instance with appropriate metadata filters

        Note:
            - If include_files provided: search ONLY in those files
            - If exclude_files provided: search in all files EXCEPT those
            - If both provided: include takes precedence (exclude is ignored)
        """
        # Build metadata filter
        filter_conditions: Dict[str, Any] = {"source": user_id}

        if include_files:
            # Restrict to specific files only
            filter_conditions = {
                "$and": [
                    {"source": user_id},
                    {"original_filename": {"$in": include_files}},
                ]
            }
            logger.debug(f"🔍 Retriever filter: INCLUDE files {include_files}")
        elif exclude_files:
            # Exclude specific files
            filter_conditions = {
                "$and": [
                    {"source": user_id},
                    {"original_filename": {"$nin": exclude_files}},
                ]
            }
            logger.debug(f"🔍 Retriever filter: EXCLUDE files {exclude_files}")
        else:
            logger.debug(f"🔍 Retriever filter: ALL files for user {user_id}")

        return self.vector_store.as_retriever(
            search_kwargs={"filter": filter_conditions, "k": k}
        )

    # --- DELETE Operations ---

    def delete_document(self, user_id: str, filename: str) -> int:
        """
        Delete all chunks of a specific document for a user.

        Uses optimized where-based deletion (single operation).

        Args:
            user_id: The user ID who owns the document
            filename: The filename to delete

        Returns:
            Number of chunks deleted (approximate, based on count before deletion)
        """
        try:
            # Count first for logging
            count_results = self.collection.get(
                where={"$and": [{"source": user_id}, {"original_filename": filename}]},
                limit=100000,
            )
            chunks_count = len(count_results.get("ids", []))

            # Delete using optimized where clause
            self.collection.delete(
                where={"$and": [{"source": user_id}, {"original_filename": filename}]}
            )

            logger.info(f"✅ Deleted ~{chunks_count} chunks for document '{filename}'")
            return chunks_count

        except Exception as e:
            logger.error(f"❌ Failed to delete document '{filename}': {e}")
            raise

    def delete_all_user_documents(self, user_id: str) -> int:
        """
        Delete all documents for a specific user.

        Uses optimized single-operation deletion.

        Args:
            user_id: The user ID whose documents should be deleted

        Returns:
            Approximate number of chunks deleted
        """
        try:
            # Count first for logging
            count_results = self.collection.get(where={"source": user_id}, limit=100000)
            total_chunks = len(count_results.get("ids", []))

            # Delete all user documents in one operation
            self.collection.delete(where={"source": user_id})

            logger.info(
                f"✅ Deleted all documents for user {user_id} (~{total_chunks} chunks)"
            )
            return total_chunks

        except Exception as e:
            logger.error(f"❌ Failed to delete all documents for user {user_id}: {e}")
            raise
