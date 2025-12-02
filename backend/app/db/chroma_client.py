"""
ChromaDB Client Module - Database Initialization and Configuration

This module provides:
- ChromaDB client initialization with persistent storage
- Embedding function setup (HuggingFace local model with singleton pattern)
- FastAPI dependency functions for dependency injection
- Type-safe interfaces for database operations

Architecture: Dependency Injection pattern for microservices-ready architecture
"""

from typing import Generator

from app.core.config import settings
from app.core.logging import logger
from chromadb import Collection, PersistentClient
from chromadb.api import ClientAPI
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

# Collection name - equivalent to a "table" in traditional databases
COLLECTION_NAME: str = "document_intelligence_collection"

# Global singleton for embedding function (loaded once at startup)
_embedding_function_singleton: HuggingFaceEmbeddings | None = None


# --- Embedding Function Configuration ---


def get_embedding_function() -> HuggingFaceEmbeddings:
    """
    Returns the local HuggingFace embedding function optimized for speed and privacy.

    Uses singleton pattern to ensure model is loaded only once at startup,
    avoiding "meta tensor" errors and improving performance.

    Benefits:
    - FREE: No API costs
    - FAST: Internal parallelism optimized with batch_size=32
    - PRIVATE: Data never sent to third-party services

    Model: sentence-transformers/all-MiniLM-L6-v2
    - 384 dimensions (compact and efficient)
    - Excellent for semantic search tasks
    - Well-balanced speed/accuracy tradeoff

    Returns:
        HuggingFaceEmbeddings: Configured embedding function (singleton)
    """
    global _embedding_function_singleton

    # Return cached instance if already initialized
    if _embedding_function_singleton is not None:
        return _embedding_function_singleton

    # Initialize on first call
    try:
        logger.info("🔧 Initializing HuggingFace embedding model (first time)...")
        _embedding_function_singleton = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={
                "device": "cpu",  # Use CPU for compatibility
            },
            encode_kwargs={
                "normalize_embeddings": True,  # L2 normalization for cosine similarity
                "batch_size": 32,  # Process 32 texts at a time for efficiency
            },
        )
        logger.info("✅ HuggingFace embedding function initialized successfully")
        return _embedding_function_singleton
    except Exception as e:
        logger.error(f"❌ Failed to initialize embedding function: {e}")
        raise


# --- ChromaDB Client Initialization ---


def get_chroma_client() -> ClientAPI:
    """
    Initializes and returns the ChromaDB persistent client.

    The client is configured with a persistent storage path from settings,
    ensuring data survives across application restarts.

    Returns:
        ClientAPI: ChromaDB client instance with persistent storage
    """
    client = PersistentClient(path=settings.CHROMA_DB_PATH)
    logger.debug(f"📊 ChromaDB client initialized with path: {settings.CHROMA_DB_PATH}")
    return client


def get_chroma_collection(client: ClientAPI) -> Collection:
    """
    Retrieves or creates the ChromaDB collection for document storage.

    This function ensures the collection exists and returns a reference to it.
    The collection is created if it doesn't exist on first access.

    Args:
        client: ChromaDB persistent client instance

    Returns:
        Collection: ChromaDB collection for RAG operations
    """
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        # Note: Embedding function is managed by LangChain wrapper, not here
    )
    logger.debug(f"📚 Collection '{COLLECTION_NAME}' ready for operations")
    return collection


# --- FastAPI Dependency Functions (Dependency Injection) ---


def get_vector_store() -> Generator[Chroma, None, None]:
    """
    FastAPI dependency that provides a LangChain Chroma vector store instance.

    This is the primary dependency for service layer injection. It creates a
    fully configured vector store with:
    - ChromaDB client connection
    - HuggingFace embedding function
    - Proper resource management (generator pattern)

    Architecture Benefits:
    - Services receive ready-to-use vector store via DI
    - No need for services to manage client lifecycle
    - Easy to mock for testing
    - Microservices-ready: can be replaced with remote vector store

    Yields:
        Chroma: LangChain vector store wrapper around ChromaDB

    Example:
        @router.post("/upload/")
        async def upload(
            vector_store: Chroma = Depends(get_vector_store)
        ):
            # Use vector_store here
            ...
    """
    try:
        # Initialize ChromaDB client
        chroma_client = get_chroma_client()

        # Get embedding function
        embedding_function = get_embedding_function()

        # Create LangChain Chroma wrapper
        vector_store = Chroma(
            client=chroma_client,
            collection_name=COLLECTION_NAME,
            embedding_function=embedding_function,
        )

        logger.debug("✅ Vector store dependency injected successfully")

        # Yield the vector store to the requesting service
        yield vector_store

    except Exception as e:
        logger.error(f"❌ Failed to initialize vector store: {e}")
        raise
    finally:
        # Cleanup resources (if needed in future versions)
        logger.debug("🔄 Vector store dependency cleanup complete")


def get_chroma_collection_direct() -> Generator[Collection, None, None]:
    """
    FastAPI dependency that provides direct access to ChromaDB collection.

    Use this when you need low-level ChromaDB operations that bypass
    the LangChain wrapper (e.g., metadata-only queries, bulk operations).

    For most RAG operations, prefer get_vector_store() instead.

    Yields:
        Collection: Direct ChromaDB collection instance

    Example:
        @router.get("/documents/")
        def list_documents(
            collection: Collection = Depends(get_chroma_collection_direct)
        ):
            # Direct ChromaDB operations
            results = collection.get(where={"user_id": "123"})
            ...
    """
    try:
        chroma_client = get_chroma_client()
        collection = get_chroma_collection(chroma_client)

        logger.debug("✅ ChromaDB collection dependency injected successfully")

        yield collection

    except Exception as e:
        logger.error(f"❌ Failed to get ChromaDB collection: {e}")
        raise
    finally:
        logger.debug("🔄 ChromaDB collection dependency cleanup complete")
