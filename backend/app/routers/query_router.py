"""
Query Router - RAG Query and Conversation Endpoints

Handles query operations:
- Query documents with RAG
- Summarize conversations
- File filtering and query optimization
"""

import asyncio
import time
import traceback
from typing import Tuple

from app.core.auth import verify_firebase_token
from app.core.logging import logger
from app.routers.auth_router import load_app_config
from app.schemas.rag_schema import (
    QueryRequest,
    QueryResponse,
    SummarizeRequest,
    SummarizeResponse,
)
from app.services.query_parser_service import query_parser_service
from app.services.query_concurrency_limiter import query_concurrency_limiter
from app.services.rag_orchestrator_service import RAGService, get_rag_service
from app.services.usage_tracking_service import UsageTrackingService, get_usage_service
from fastapi import APIRouter, Depends, HTTPException, status
from firebase_admin import auth


def _get_user_tier_limits(user_id: str) -> Tuple[str, int]:
    """
    Get user tier and query limits from Firebase.

    Args:
        user_id: Firebase user ID

    Returns:
        Tuple of (tier, max_queries_per_day)
    """
    user = auth.get_user(user_id)
    custom_claims = user.custom_claims or {}
    tier = custom_claims.get("tier", "FREE")

    logger.info(f"🎫 User ID: {user_id}")
    logger.info(f"🎫 User tier: {tier}")
    logger.info(f"🎫 All custom claims: {custom_claims}")

    # Load tier limits from Firestore
    app_config = load_app_config()

    if tier == "UNLIMITED":
        max_queries = 9999
        logger.info(f"✅ UNLIMITED tier detected - max_queries set to {max_queries}")
    else:
        tier_limits = app_config["limits"].get(tier, app_config["limits"]["FREE"])
        max_queries = tier_limits["max_queries_per_day"]
        logger.info(f"📊 Tier limits for {tier}: {max_queries} queries/day")

    return tier, max_queries


def _reserve_and_enforce_query_limit(
    usage_service: UsageTrackingService, user_id: str, tier: str, max_queries: int
) -> int:
    """
    Atomically reserve quota before starting RAG/OpenAI work.

    Args:
        usage_service: Usage tracking service
        user_id: Firebase user ID
        tier: User tier
        max_queries: Maximum queries allowed per day

    Returns:
        Reserved query count

    Raises:
        HTTPException: If query limit is exceeded
    """
    can_query, reserved_count = usage_service.reserve_query_slot(
        user_id, max_queries
    )
    logger.info(
        f"📊 Usage reservation result: reserved={can_query}, "
        f"queries_used={reserved_count}, max_queries={max_queries}"
    )

    if not can_query:
        logger.warning(
            f"⛔ Query limit exceeded for user {user_id} ({tier}): "
            f"{reserved_count}/{max_queries}"
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                f"Daily query limit exceeded ({reserved_count}/{max_queries}). "
                f"Please upgrade your plan or try again tomorrow."
            ),
        )

    logger.info(
        f"✅ Query slot reserved: {reserved_count}/{max_queries} ({tier})"
    )
    return reserved_count


def _log_request_details(request: QueryRequest, user_id: str) -> None:
    """
    Log detailed request information.

    Args:
        request: Query request
        user_id: Firebase user ID
    """
    logger.info(f"{'='*80}")
    logger.info("📥 [ROUTER] NEW QUERY REQUEST")
    logger.info(f"{'='*80}")
    logger.info(f"👤 User ID: {user_id}")
    logger.info(f"❓ Query: {request.query}")
    logger.info(
        f"📜 Conversation History: {len(request.conversation_history)} messages"
    )

    if request.conversation_history:
        for idx, msg in enumerate(request.conversation_history[-3:], 1):
            logger.debug(f"   [{idx}] {msg.role}: {msg.content[:80]}...")

    if request.output_language:
        logger.info(f"🌍 Output Language: {request.output_language}")
    else:
        logger.info("🌍 Output Language: Not specified (will auto-detect from query)")

    logger.info(f"{'='*80}")


def _log_response_details(
    answer: str, sources: list[str], tier: str, new_count: int, max_queries: int
) -> None:
    """
    Log detailed response information.

    Args:
        answer: Generated answer
        sources: Source documents list
        tier: User tier
        new_count: Updated query count
        max_queries: Maximum queries allowed
    """
    logger.info(f"{'='*80}")
    logger.info("📤 [ROUTER] QUERY RESPONSE")
    logger.info(f"{'='*80}")
    logger.info(f"✅ Answer length: {len(answer)} characters")
    logger.info(f"📚 Sources: {len(sources)} documents")
    if sources:
        logger.info(f"   Files: {', '.join(sources[:5])}")
    logger.info(f"📝 Answer preview: {answer[:200]}...")
    logger.info(f"📊 Query slot reserved: {new_count}/{max_queries} ({tier})")
    logger.info(f"{'='*80}")


router = APIRouter(prefix="/rag", tags=["query"])


@router.post("/query/", response_model=QueryResponse)
async def query_document(
    request: QueryRequest,
    user_id: str = Depends(verify_firebase_token),
    rag_service: RAGService = Depends(get_rag_service),
) -> QueryResponse:
    """
    **Query documents using RAG (Retrieval-Augmented Generation).**

    Features:
    - Automatic file filtering from natural language (e.g., "only in file X")
    - Grammar correction and query optimization
    - Conversation history support
    - Multi-language support
    - Tier-based rate limiting

    **Cost:** ~$0.00007 per query for optimization (7 cents per 1000 queries)
    """
    query_slot_acquired = await query_concurrency_limiter.acquire(user_id)
    if not query_slot_acquired:
        logger.warning(
            f"⛔ Concurrent RAG query rejected for user {user_id}: "
            "a query is already running"
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="A query is already running for this account. Please wait for it to finish.",
            headers={"Retry-After": "5"},
        )

    quota_reserved = False
    try:
        request_started = time.perf_counter()
        _log_request_details(request, user_id)

        # Reserve tier quota before any parser/RAG/OpenAI work.
        tier_started = time.perf_counter()
        tier, max_queries = await asyncio.to_thread(_get_user_tier_limits, user_id)
        usage_service = get_usage_service()
        reserved_count = await asyncio.to_thread(
            _reserve_and_enforce_query_limit,
            usage_service,
            user_id,
            tier,
            max_queries,
        )
        quota_reserved = True
        logger.info(
            f"⏱️ Query timing | firebase_tier_and_usage="
            f"{(time.perf_counter() - tier_started) * 1000:.2f}ms"
        )

        # Extract file filters and optimize query
        documents_started = time.perf_counter()
        available_documents = await asyncio.to_thread(
            rag_service.get_user_documents, user_id
        )
        available_filenames = [doc.filename for doc in available_documents]

        logger.info(f"📂 User has {len(available_filenames)} documents available")
        logger.info("🔍 Extracting file filters and optimizing query...")
        logger.info(
            f"⏱️ Query timing | document_lookup="
            f"{(time.perf_counter() - documents_started) * 1000:.2f}ms"
        )

        parser_started = time.perf_counter()
        filter_result = await asyncio.to_thread(
            query_parser_service.extract_file_filters,
            query=request.query,
            available_files=available_filenames,
        )
        logger.info(
            f"⏱️ Query timing | query_parser="
            f"{(time.perf_counter() - parser_started) * 1000:.2f}ms"
        )

        query_for_rag = filter_result.cleaned_query
        include_files = (
            filter_result.include_files if filter_result.include_files else None
        )
        exclude_files = (
            filter_result.exclude_files if filter_result.exclude_files else None
        )

        logger.info(
            f"✅ File filters: include={include_files}, exclude={exclude_files}"
        )
        logger.info(f"🧹 Optimized query: {query_for_rag}")

        # Call RAG service
        rag_started = time.perf_counter()
        answer, sources = await asyncio.to_thread(
            rag_service.answer_query,
            query_for_rag,
            user_id,
            request.conversation_history,
            request.output_language,
            include_files=include_files,
            exclude_files=exclude_files,
        )
        logger.info(
            f"⏱️ Query timing | rag_answer="
            f"{(time.perf_counter() - rag_started) * 1000:.2f}ms"
        )

        logger.info(
            f"⏱️ Query timing | total="
            f"{(time.perf_counter() - request_started) * 1000:.2f}ms"
        )
        _log_response_details(answer, sources, tier, reserved_count, max_queries)

        return QueryResponse(answer=answer, source_documents=sources)

    except HTTPException:
        raise
    except Exception as e:
        if quota_reserved:
            logger.warning(
                "⚠️ RAG request failed after quota reservation; retaining the "
                "reserved slot because external work may already have started."
            )
        logger.error(f"{'='*80}")
        logger.error("❌ [ROUTER] QUERY PROCESSING ERROR")
        logger.error(f"{'='*80}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error message: {str(e)}")
        logger.error(f"Traceback:\n{traceback.format_exc()}")
        logger.error(f"{'='*80}")

        # Return more detailed error message for debugging
        error_detail = f"Failed to process query: {type(e).__name__}: {str(e)}"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_detail,
        ) from e
    finally:
        await query_concurrency_limiter.release(user_id)


@router.post("/summarize/", response_model=SummarizeResponse)
def summarize_conversation(
    request: SummarizeRequest,
    user_id: str = Depends(verify_firebase_token),
    rag_service: RAGService = Depends(get_rag_service),
) -> SummarizeResponse:
    """
    **Generate conversation summary for long-term memory.**

    - Extracts key facts and topics
    - Useful for conversation history compression
    - Stored in Firestore for context retrieval
    """
    try:
        logger.info(f"📝 Generating summary for user {user_id}")
        summary = rag_service.generate_conversation_summary(
            request.conversation_history
        )
        return SummarizeResponse(summary=summary)
    except Exception as e:
        logger.error(f"Summarization error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate conversation summary.",
        ) from e
