"""
Query Router - RAG Query and Conversation Endpoints

Handles query operations:
- Query documents with RAG
- Summarize conversations
- File filtering and query optimization
"""

import asyncio
import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.config.security_constants import LLM_TIMEOUT_SECONDS
from app.core.auth import require_verified_email
from app.core.logging import logger
from app.dependencies import (
    get_query_quota_service,
    get_rag_service,
    query_parser_service,
)
from app.schemas.rag_schema import (
    QueryRequest,
    QueryResponse,
    SourceCitation,
    SummarizeRequest,
    SummarizeResponse,
)
from app.services.query_concurrency_limiter import (
    global_expensive_operation_limiter,
    query_concurrency_limiter,
)
from app.services.query_quota_service import QueryLimitExceededError, QueryQuotaService
from app.services.rag_orchestrator_service import RAGService


def _log_request_details(request: QueryRequest, user_id: str) -> None:
    """
    Log detailed request information.

    Args:
        request: Query request
        user_id: Firebase user ID
    """
    del user_id
    logger.debug(
        "RAG request received | History messages: {} | Output language provided: {}",
        len(request.conversation_history),
        bool(request.output_language),
    )


def _normalize_citations(sources: list[Any]) -> list[SourceCitation]:
    """Preserve structured retrieval citations and keep legacy filename mocks compatible."""
    citations: list[SourceCitation] = []
    seen: set[tuple[str, int | None]] = set()
    for source in sources:
        if isinstance(source, str):
            citation = SourceCitation(filename=source)
        elif isinstance(source, dict):
            try:
                citation = SourceCitation.model_validate(source)
            except ValueError:
                continue
        else:
            continue
        citation_key = (citation.filename, citation.page_number)
        if citation_key not in seen:
            seen.add(citation_key)
            citations.append(citation)
    return citations[:5]


def _log_response_details(
    answer: str,
    citations: list[SourceCitation],
    tier: str,
    new_count: int,
    max_queries: int,
) -> None:
    """
    Log detailed response information.

    Args:
        answer: Generated answer
        citations: Retrieved source citations
        tier: User tier
        new_count: Updated query count
        max_queries: Maximum queries allowed
    """
    logger.debug(
        "RAG response completed | Answer characters: {} | Citations: {} | "
        "Quota: {}/{} | Tier: {}",
        len(answer),
        len(citations),
        new_count,
        max_queries,
        tier,
    )


router = APIRouter(prefix="/rag", tags=["query"])


async def _run_provider_operation(operation: Any, *args: Any, **kwargs: Any) -> Any:
    """Run one blocking RAG operation with the public provider deadline."""
    try:
        async with asyncio.timeout(LLM_TIMEOUT_SECONDS):
            return await asyncio.to_thread(operation, *args, **kwargs)
    except TimeoutError as exc:
        logger.warning("Provider-backed operation timed out")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="The language service timed out. Please try again.",
        ) from exc


@router.post("/query/", response_model=QueryResponse)
async def query_document(
    request: QueryRequest,
    user_id: str = Depends(require_verified_email),
    rag_service: RAGService = Depends(get_rag_service),
    quota_service: QueryQuotaService = Depends(get_query_quota_service),
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
    global_slot_acquired = await global_expensive_operation_limiter.acquire()
    if not global_slot_acquired:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="The public demo is currently at capacity. Please try again in a few minutes.",
            headers={"Retry-After": "120"},
        )
    query_slot_acquired = await query_concurrency_limiter.acquire(user_id)
    if not query_slot_acquired:
        logger.warning("Concurrent RAG query rejected")
        await global_expensive_operation_limiter.release()
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="A query is already running for this account. Please wait for it to finish.",
            headers={"Retry-After": "5"},
        )

    quota_reserved = False
    worker_started = False
    worker_entered = False
    leases_released = False

    async def release_worker_leases() -> None:
        """Release the worker-owned slots exactly once after real work ends."""
        nonlocal leases_released
        if leases_released:
            return
        leases_released = True
        await query_concurrency_limiter.release(user_id)
        await global_expensive_operation_limiter.release()

    try:

        def run_rag_worker() -> tuple[Any, Any, Any]:
            """Run every potentially billable step under one worker-owned lease."""
            nonlocal quota_reserved
            request_started = time.perf_counter()
            _log_request_details(request, user_id)

            tier_started = time.perf_counter()
            reservation = quota_service.reserve(user_id)
            quota_reserved = True
            logger.debug(
                "Query timing | tier and usage: {:.2f}ms",
                (time.perf_counter() - tier_started) * 1000,
            )

            documents_started = time.perf_counter()
            available_documents = rag_service.get_user_documents(user_id)
            available_filenames = [doc.filename for doc in available_documents]
            logger.debug(
                "Document lookup completed | Available documents: {}",
                len(available_filenames),
            )
            logger.debug(
                "Query timing | document lookup: {:.2f}ms",
                (time.perf_counter() - documents_started) * 1000,
            )

            parser_started = time.perf_counter()
            filter_result = query_parser_service.extract_file_filters(
                query=request.query, available_files=available_filenames
            )
            logger.debug(
                "Query timing | query parser: {:.2f}ms",
                (time.perf_counter() - parser_started) * 1000,
            )

            include_files = filter_result.include_files or None
            exclude_files = filter_result.exclude_files or None
            logger.debug(
                "File filters resolved | Included: {} | Excluded: {}",
                len(include_files or []),
                len(exclude_files or []),
            )
            rag_kwargs: dict[str, Any] = {
                "include_files": include_files,
                "exclude_files": exclude_files,
                "raw_user_query": request.query,
            }
            if filter_result.is_compound:
                rag_kwargs["retrieval_queries"] = filter_result.retrieval_queries
            rag_started = time.perf_counter()
            answer, sources = rag_service.answer_query(
                filter_result.cleaned_query,
                user_id,
                request.conversation_history,
                request.output_language,
                **rag_kwargs,
            )
            logger.debug(
                "Query timing | RAG answer: {:.2f}ms",
                (time.perf_counter() - rag_started) * 1000,
            )
            logger.debug(
                "Query timing | total: {:.2f}ms",
                (time.perf_counter() - request_started) * 1000,
            )
            return reservation, answer, sources

        event_loop = asyncio.get_running_loop()

        def worker_with_lease() -> tuple[Any, Any, Any]:
            nonlocal worker_entered
            worker_entered = True
            try:
                return run_rag_worker()
            finally:
                # asyncio cancellation cannot stop a running thread. Schedule
                # release from the thread only after all paid work has ended.
                event_loop.call_soon_threadsafe(
                    lambda: asyncio.create_task(release_worker_leases())
                )

        worker_started = True
        worker_task = asyncio.create_task(asyncio.to_thread(worker_with_lease))

        def release_if_worker_never_started(_task: asyncio.Task[Any]) -> None:
            if not worker_entered:
                asyncio.create_task(release_worker_leases())

        worker_task.add_done_callback(release_if_worker_never_started)
        try:
            async with asyncio.timeout(LLM_TIMEOUT_SECONDS):
                reservation, answer, sources = await asyncio.shield(worker_task)
        except TimeoutError as exc:
            logger.warning("Provider-backed operation timed out")
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="The language service timed out. Please try again.",
            ) from exc
        citations = _normalize_citations(sources)
        source_documents = list(
            dict.fromkeys(citation.filename for citation in citations)
        )
        _log_response_details(
            answer,
            citations,
            reservation.tier,
            reservation.reserved_count,
            reservation.max_queries,
        )

        return QueryResponse(
            answer=answer, source_documents=source_documents, citations=citations
        )

    except QueryLimitExceededError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(exc),
        ) from exc
    except HTTPException:
        raise
    except Exception as e:
        if quota_reserved:
            logger.warning(
                "⚠️ RAG request failed after quota reservation; retaining the "
                "reserved slot because external work may already have started."
            )
        logger.error("RAG query failed | Type: {}", type(e).__name__)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to process the query. Please try again.",
        ) from e
    finally:
        if not worker_started:
            await release_worker_leases()


@router.post("/summarize/", response_model=SummarizeResponse)
async def summarize_conversation(
    request: SummarizeRequest,
    user_id: str = Depends(require_verified_email),
    rag_service: RAGService = Depends(get_rag_service),
    quota_service: QueryQuotaService = Depends(get_query_quota_service),
) -> SummarizeResponse:
    """
    **Generate conversation summary for long-term memory.**

    - Extracts key facts and topics
    - Useful for conversation history compression
    - Stored in Firestore for context retrieval
    """
    global_slot_acquired = await global_expensive_operation_limiter.acquire()
    if not global_slot_acquired:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="The public demo is currently at capacity. Please try again in a few minutes.",
            headers={"Retry-After": "120"},
        )
    slot_acquired = await query_concurrency_limiter.acquire(user_id)
    if not slot_acquired:
        await global_expensive_operation_limiter.release()
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="A query is already running for this account. Please wait for it to finish.",
            headers={"Retry-After": "5"},
        )
    quota_reserved = False
    try:
        await asyncio.to_thread(quota_service.reserve, user_id)
        quota_reserved = True
        logger.info("📝 Generating bounded conversation summary")
        summary = await _run_provider_operation(
            rag_service.generate_conversation_summary, request.conversation_history
        )
        return SummarizeResponse(summary=summary)
    except QueryLimitExceededError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(exc),
        ) from exc
    except HTTPException:
        raise
    except Exception as exc:
        if quota_reserved:
            logger.warning("⚠️ Summary failed after quota reservation; retaining slot")
        logger.error("❌ Conversation summarization failed; details redacted")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to generate the conversation summary. Please try again.",
        ) from exc
    finally:
        await query_concurrency_limiter.release(user_id)
        await global_expensive_operation_limiter.release()
