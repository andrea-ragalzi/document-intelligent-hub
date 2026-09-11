"""Application-facing ports for outbound document persistence and retrieval."""

from typing import Any, List, Protocol, Tuple

from langchain_core.documents import Document


class VectorStorePort(Protocol):
    """Operations the application needs from a vector store adapter."""

    def add_documents(self, documents: List[Document], batch_size: int = 2000) -> int:
        """Persist document chunks and return the number written."""

    def check_document_exists(self, user_id: str, filename: str) -> bool:
        """Check whether a user's document is indexed."""

    def get_user_chunks_sample(
        self, user_id: str, sample_size: int = 10000
    ) -> Tuple[List[dict[str, Any]], List[str]]:
        """Return metadata and identifiers for a user's indexed chunks."""

    def delete_document(self, user_id: str, filename: str) -> int:
        """Delete all chunks belonging to one document."""

    def delete_all_user_documents(self, user_id: str) -> int:
        """Delete all chunks belonging to one user."""

    def get_retriever(self, **kwargs: Any) -> Any:
        """Build the adapter's tenant-scoped retriever."""

    def lexical_candidate_search(
        self, user_id: str, terms: List[str], limit_per_term: int = 20
    ) -> List[Document]:
        """Return bounded lexical candidates for reranking."""
