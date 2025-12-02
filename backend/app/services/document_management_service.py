"""
Document Management Service

Handles CRUD operations for user documents.
Extracted from RAGService as part of service splitting (200-300 lines per service).

Responsibilities:
- List user documents with metadata
- Delete individual documents
- Delete all user documents
- Count user documents
"""

from typing import List

from app.core.logging import logger
from app.repositories.vector_store_repository import VectorStoreRepository
from app.schemas.rag_schema import DocumentInfo


class DocumentManagementService:
    """
    Specialized service for document management operations.

    Part of RAGService refactoring to maintain 200-300 lines per service.
    Provides CRUD operations for user documents.
    """

    def __init__(self, repository: VectorStoreRepository) -> None:
        """
        Initialize DocumentManagementService.

        Args:
            repository: Vector store repository for document operations
        """
        self.repository = repository

    def get_user_documents(self, user_id: str) -> List[DocumentInfo]:
        """
        Get list of all documents for a user with metadata.

        Aggregates chunks by filename and returns summary information
        including chunk count, language, and upload timestamp.

        Args:
            user_id: The user ID

        Returns:
            List of DocumentInfo objects with filename, chunks_count, language, uploaded_at
        """
        try:
            # Get large sample to ensure all documents are discovered
            metadatas, _ = self.repository.get_user_chunks_sample(
                user_id, sample_size=100000
            )

            if not metadatas:
                logger.info(f"📂 No documents found for user {user_id}")
                return []

            logger.debug(f"📊 Processing {len(metadatas)} metadata entries")

            # Group chunks by filename
            documents_map = {}
            for metadata in metadatas:
                filename = metadata.get("original_filename", "Unknown")

                if filename not in documents_map:
                    documents_map[filename] = {
                        "filename": filename,
                        "language": metadata.get("original_language_code", "unknown"),
                        "uploaded_at": metadata.get("uploaded_at"),
                        "chunks": 1,
                    }
                else:
                    documents_map[filename]["chunks"] += 1

            # Convert to DocumentInfo list
            documents = [
                DocumentInfo(
                    filename=doc["filename"],
                    chunks_count=doc["chunks"],
                    language=doc["language"],
                    uploaded_at=str(doc["uploaded_at"]) if doc["uploaded_at"] else None,
                )
                for doc in documents_map.values()
            ]

            logger.info(
                f"📚 Found {len(documents)} unique documents for user {user_id}"
            )
            logger.debug(f"   Documents: {[d.filename for d in documents]}")
            return documents

        except Exception as e:
            logger.error(f"❌ Error getting user documents: {e}")
            return []

    def delete_user_document(self, user_id: str, filename: str) -> int:
        """
        Delete a specific document for a user.

        Removes all chunks associated with the document from the vector store.

        Args:
            user_id: The user ID
            filename: The filename to delete

        Returns:
            Number of chunks deleted
        """
        try:
            chunks_deleted = self.repository.delete_document(user_id, filename)
            logger.info(f"✅ Deleted {chunks_deleted} chunks for document '{filename}'")
            return chunks_deleted
        except Exception as e:
            logger.error(f"❌ Error deleting document '{filename}': {e}")
            raise

    def delete_all_user_documents(self, user_id: str) -> int:
        """
        Delete all documents for a user.

        Removes all chunks for the user from the vector store.
        Used when user deletes account or requests full data removal.

        Args:
            user_id: The user ID

        Returns:
            Number of chunks deleted
        """
        try:
            chunks_deleted = self.repository.delete_all_user_documents(user_id)
            logger.info(
                f"✅ Deleted all documents for user {user_id} ({chunks_deleted} chunks)"
            )
            return chunks_deleted
        except Exception as e:
            logger.error(f"❌ Error deleting all documents for user {user_id}: {e}")
            raise

    def get_user_document_count(self, user_id: str) -> int:
        """
        Count the number of unique documents for a user.

        Used for quota limits and UI display.

        Args:
            user_id: The user ID

        Returns:
            Number of unique documents
        """
        try:
            # Get sample and count unique filenames
            metadatas, _ = self.repository.get_user_chunks_sample(
                user_id, sample_size=100000
            )

            if not metadatas:
                return 0

            unique_filenames = {
                metadata.get("original_filename", "Unknown") for metadata in metadatas
            }

            count = len(unique_filenames)
            logger.info(f"📊 User {user_id} has {count} documents")
            return count

        except Exception as e:
            logger.error(f"❌ Error counting user documents: {e}")
            return 0
