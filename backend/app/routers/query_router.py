"""
Query Router - RAG Query and Conversation Endpoints

Handles query operations:
- Query documents with RAG
- Summarize conversations
- File filtering and query optimization
"""

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


def _check_and_enforce_query_limit(
    usage_service: UsageTrackingService,
    user_id: str,
    tier: str,
    max_queries: int
) -> int:
    """
    Check if user has exceeded query limit and raise exception if so.

    Args:
        usage_service: Usage tracking service
        user_id: Firebase user ID
        tier: User tier
        max_queries: Maximum queries allowed per day

    Returns:
        Current queries used count

    Raises:
        HTTPException: If query limit is exceeded
    """
    can_query, queries_used = usage_service.check_query_limit(user_id, max_queries)
    logger.info(
        f"📊 Usage check result: can_query={can_query}, "
        f"queries_used={queries_used}, max_queries={max_queries}"
    )

    if not can_query:
        logger.warning(
            f"⛔ Query limit exceeded for user {user_id} ({tier}): "
            f"{queries_used}/{max_queries}"
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                f"Daily query limit exceeded ({queries_used}/{max_queries}). "
                f"Please upgrade your plan or try again tomorrow."
            )
        )

    logger.info(f"✅ Query limit check passed: {queries_used}/{max_queries} ({tier})")
    return queries_used


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
    logger.info(f"📜 Conversation History: {len(request.conversation_history)} messages")

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
    logger.info(f"📊 Query counter incremented: {new_count}/{max_queries} ({tier})")
    logger.info(f"{'='*80}")


router = APIRouter(prefix="/rag", tags=["query"])


@router.post("/query/", response_model=QueryResponse)
async def query_document(
    request: QueryRequest,
    user_id: str = Depends(verify_firebase_token),
    rag_service: RAGService = Depends(get_rag_service),
):
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
    try:
        _log_request_details(request, user_id)

        # Check tier limits and usage
        tier, max_queries = _get_user_tier_limits(user_id)
        usage_service = get_usage_service()
        _check_and_enforce_query_limit(usage_service, user_id, tier, max_queries)

        # Extract file filters and optimize query
        available_documents = rag_service.get_user_documents(user_id)
        available_filenames = [doc.filename for doc in available_documents]

        logger.info(f"📂 User has {len(available_filenames)} documents available")
        logger.info("🔍 Extracting file filters and optimizing query...")

        filter_result = query_parser_service.extract_file_filters(
            query=request.query,
            available_files=available_filenames
        )

        query_for_rag = filter_result.cleaned_query
        include_files = filter_result.include_files if filter_result.include_files else None
        exclude_files = filter_result.exclude_files if filter_result.exclude_files else None

        logger.info(f"✅ File filters: include={include_files}, exclude={exclude_files}")
        logger.info(f"🧹 Optimized query: {query_for_rag}")

        # Call RAG service
        answer, sources = rag_service.answer_query(
            query_for_rag,
            user_id,
            request.conversation_history,
            request.output_language,
            include_files=include_files,
            exclude_files=exclude_files
        )

        # Increment query counter
        new_count = usage_service.increment_user_queries(user_id)
        _log_response_details(answer, sources, tier, new_count, max_queries)

        return QueryResponse(answer=answer, source_documents=sources)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"{'='*80}")
        logger.error("❌ [ROUTER] QUERY PROCESSING ERROR")
        logger.error(f"{'='*80}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error message: {str(e)}")
        logger.error(f"Traceback:\n{traceback.format_exc()}")
        logger.error(f"{'='*80}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process query and retrieve answer.",
        ) from e


@router.post("/summarize/", response_model=SummarizeResponse)
def summarize_conversation(
    request: SummarizeRequest,
    user_id: str = Depends(verify_firebase_token),
    rag_service: RAGService = Depends(get_rag_service),
):
    """
    **Generate conversation summary for long-term memory.**

    - Extracts key facts and topics
    - Useful for conversation history compression
    - Stored in Firestore for context retrieval
    """
    try:
        logger.info(f"📝 Generating summary for user {user_id}")
        summary = rag_service.generate_conversation_summary(request.conversation_history)
        return SummarizeResponse(summary=summary)
    except Exception as e:
        logger.error(f"Summarization error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate conversation summary.",
        ) from e
