"""FastAPI composition root for application services and outbound adapters."""

from collections.abc import Generator

from chromadb import Collection
from fastapi import Depends
from firebase_admin import auth
from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from app.core.config import settings
from app.core.llm_configuration import chat_model_options
from app.db.chroma_client import get_chroma_collection_direct, get_vector_store
from app.ports.vector_store import VectorStorePort
from app.repositories.vector_store_repository import VectorStoreRepository
from app.infrastructure.firebase_config import load_app_config
from app.services.query_quota_service import QueryQuotaService
from app.services.rag_orchestrator_service import RAGService
from app.services.usage_tracking_service import get_usage_service


def get_vector_store_repository(
    vector_store: Chroma = Depends(get_vector_store),
    collection: Collection = Depends(get_chroma_collection_direct),
) -> Generator[VectorStoreRepository, None, None]:
    """Wire Chroma clients to the application-facing vector store port."""
    yield VectorStoreRepository(vector_store=vector_store, collection=collection)


def _get_firebase_user_tier(user_id: str) -> str:
    """Read the tier claim at the Firebase boundary."""
    user = auth.get_user(user_id)
    custom_claims = user.custom_claims or {}
    return str(custom_claims.get("tier", "FREE"))


def get_query_quota_service() -> QueryQuotaService:
    """Wire Firebase configuration and usage persistence to quota rules."""
    return QueryQuotaService(
        tier_provider=_get_firebase_user_tier,
        limits_provider=load_app_config,
        usage_tracker=get_usage_service(),
    )


def _build_chat_model() -> ChatOpenAI:
    """Create one configured OpenAI adapter for the RAG application."""
    return ChatOpenAI(
        **chat_model_options(
            settings.LLM_MODEL,
            SecretStr(settings.OPENAI_API_KEY),
            temperature=0.0,
        )
    )


def get_rag_service(
    repository: VectorStorePort = Depends(get_vector_store_repository),
) -> RAGService:
    """Wire concrete LLM and vector adapters to the RAG application service."""
    return RAGService(
        repository=repository,
        llm=_build_chat_model(),
        query_gen_llm=_build_chat_model(),
    )
