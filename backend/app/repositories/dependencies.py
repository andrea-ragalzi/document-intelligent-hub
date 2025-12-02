"""
Repository Dependency Injection

Provides FastAPI dependencies for repository instances.
Repositories are initialized with their required dependencies.
"""

from typing import Generator

from chromadb import Collection
from fastapi import Depends
from langchain_community.vectorstores import Chroma

from app.db.chroma_client import get_chroma_collection_direct, get_vector_store
from app.repositories.vector_store_repository import VectorStoreRepository


def get_vector_store_repository(
    vector_store: Chroma = Depends(get_vector_store),
    collection: Collection = Depends(get_chroma_collection_direct),
) -> Generator[VectorStoreRepository, None, None]:
    """
    FastAPI dependency for VectorStoreRepository.

    Injects both LangChain Chroma wrapper and direct Collection access
    into the repository instance.

    Args:
        vector_store: LangChain Chroma wrapper (injected)
        collection: Direct ChromaDB collection (injected)

    Yields:
        VectorStoreRepository: Fully configured repository instance

    Example:
        @router.post("/documents/")
        def create_document(
            repository: VectorStoreRepository = Depends(get_vector_store_repository)
        ):
            repository.add_documents(docs)
    """
    yield VectorStoreRepository(vector_store=vector_store, collection=collection)
