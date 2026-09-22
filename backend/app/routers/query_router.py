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

from fastapi import APIRouter, Depends, HTTPException, Request, status
from openai import APITimeoutError

from app.core.auth import (
    WorkspaceAccess,
    get_query_workspace_access,
    require_verified_email,
)
from app.core.config import settings
from app.core.logging import logger
from app.dependencies import (
    get_guest_query_budget_service,
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
    guest_query_concurrency_limiter,
    query_concurrency_limiter,
)
from app.services.guest_query_budget_service import (
    GuestBudgetExceededError,
    GuestQueryBudgetService,
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
_background_tasks: set[asyncio.Task[Any]] = set()


def _track_background_task(task: asyncio.Task[Any]) -> None:
    """Keep a scheduled release alive until it completes."""
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)


async def _acquire_query_leases(access: WorkspaceAccess) -> None:
    """Admit a query without waiting when either concurrency limit is full."""
    global_slot_acquired = await global_expensive_operation_limiter.acquire()
    if not global_slot_acquired:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="The public demo is currently at capacity. Please try again in a few minutes.",
            headers={"Retry-After": "120"},
        )

    query_slot_acquired = await query_concurrency_limiter.acquire(access.principal_uid)
    if query_slot_acquired and not access.is_guest:
        return

    if query_slot_acquired and await guest_query_concurrency_limiter.acquire():
        return

    if query_slot_acquired:
        await query_concurrency_limiter.release(access.principal_uid)

    logger.warning("Concurrent RAG query rejected")
    await global_expensive_operation_limiter.release()
    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail="A query is already running for this account. Please wait for it to finish.",
        headers={"Retry-After": "5"},
    )


async def _execute_query_with_worker_lease(
    request: QueryRequest,
    access: WorkspaceAccess,
    rag_service: RAGService = Depends(get_rag_service),
    quota_service: Any = Depends(get_query_quota_service),
) -> QueryResponse:
    """Execute all potentially billable work under already-acquired leases."""
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
        await query_concurrency_limiter.release(access.principal_uid)
        if access.is_guest:
            await guest_query_concurrency_limiter.release()
        await global_expensive_operation_limiter.release()

    def schedule_worker_lease_release() -> None:
        release_task = asyncio.create_task(release_worker_leases())
        _track_background_task(release_task)

    try:

        def run_rag_worker() -> tuple[Any, Any, Any]:
            """Run every potentially billable step under one worker-owned lease."""
            nonlocal quota_reserved
            request_started = time.perf_counter()
            _log_request_details(request, access.principal_uid)

            tier_started = time.perf_counter()
            reservation = quota_service.reserve(access.workspace_id)
            quota_reserved = True
            logger.debug(
                "Query timing | tier and usage: {:.2f}ms",
                (time.perf_counter() - tier_started) * 1000,
            )

            documents_started = time.perf_counter()
            available_documents = rag_service.get_user_documents(access.workspace_id)
            available_filenames = [doc.filename for doc in available_documents]
            logger.debug(
                "Document lookup completed | Available documents: {}",
                len(available_filenames),
            )
            logger.debug(
                "Query timing | document lookup: {:.2f}ms",
                (time.perf_counter() - documents_started) * 1000,
            )

            deterministic_handler = getattr(rag_service, "try_deterministic_query", None)
            deterministic = (
                deterministic_handler(  # pylint: disable=not-callable
                    request.query,
                    access.workspace_id,
                    available_documents,
                    request.conversation_history,
                )
                if callable(deterministic_handler)
                else None
            )
            # Test doubles and external integrations which predate routing may
            # return arbitrary mock values. Only a complete trusted result can
            # bypass the established RAG path.
            if isinstance(deterministic, tuple) and len(deterministic) == 4:
                answer, sources, route, reason = tuple(deterministic)
                logger.info(
                    "Query route completed | route={} reason={} luna_invoked=false",
                    route,
                    reason,
                )
                return reservation, answer, sources

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
                access.workspace_id,
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
                event_loop.call_soon_threadsafe(schedule_worker_lease_release)

        worker_started = True
        worker_task = asyncio.create_task(asyncio.to_thread(worker_with_lease))

        def release_if_worker_never_started(_task: asyncio.Task[Any]) -> None:
            if not worker_entered:
                schedule_worker_lease_release()

        worker_task.add_done_callback(release_if_worker_never_started)
        try:
            async with asyncio.timeout(settings.OPENAI_TIMEOUT_SECONDS):
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

    except (QueryLimitExceededError, GuestBudgetExceededError) as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(exc),
        ) from exc
    except (TimeoutError, APITimeoutError) as exc:
        logger.warning("Provider-backed operation timed out")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="The language service timed out. Please try again.",
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


@router.post("/query/", response_model=QueryResponse)
async def query_document(
    request: QueryRequest,
    http_request: Request,
    access: WorkspaceAccess = Depends(get_query_workspace_access),
    rag_service: RAGService = Depends(get_rag_service),
    quota_service: QueryQuotaService = Depends(get_query_quota_service),
    guest_budget_service: GuestQueryBudgetService = Depends(
        get_guest_query_budget_service
    ),
) -> QueryResponse:
    """Query user documents through the bounded RAG execution path."""
    selected_quota: Any = quota_service
    if access.is_guest:
        client_ip = http_request.client.host if http_request.client else "unknown"

        class RequestGuestQuota:
            """Bind request identity facts to the shared budget service."""

            def reserve(self, _workspace_id: str) -> Any:
                return guest_budget_service.reserve(access.principal_uid, client_ip)

        selected_quota = RequestGuestQuota()
    await _acquire_query_leases(access)
    return await _execute_query_with_worker_lease(
        request, access, rag_service, selected_quota
    )


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
    worker_started = False
    worker_entered = False
    leases_released = False

    async def release_worker_leases() -> None:
        """Release leases once the synchronous provider work has actually ended."""
        nonlocal leases_released
        if leases_released:
            return
        leases_released = True
        await query_concurrency_limiter.release(user_id)
        await global_expensive_operation_limiter.release()

    def schedule_worker_lease_release() -> None:
        release_task = asyncio.create_task(release_worker_leases())
        _track_background_task(release_task)

    try:
        event_loop = asyncio.get_running_loop()

        def run_summary_worker() -> str:
            nonlocal quota_reserved
            quota_service.reserve(user_id)
            quota_reserved = True
            logger.info("📝 Generating bounded conversation summary")
            return rag_service.generate_conversation_summary(request.conversation_history)

        def worker_with_lease() -> str:
            nonlocal worker_entered
            worker_entered = True
            try:
                return run_summary_worker()
            finally:
                # Cancelling the request cannot stop this thread. Keep the
                # shared capacity lease until the provider call terminates.
                event_loop.call_soon_threadsafe(schedule_worker_lease_release)

        worker_started = True
        worker_task = asyncio.create_task(asyncio.to_thread(worker_with_lease))

        def release_if_worker_never_started(_task: asyncio.Task[Any]) -> None:
            if not worker_entered:
                schedule_worker_lease_release()

        worker_task.add_done_callback(release_if_worker_never_started)
        try:
            async with asyncio.timeout(settings.OPENAI_TIMEOUT_SECONDS):
                summary = await asyncio.shield(worker_task)
        except TimeoutError as exc:
            logger.warning("Provider-backed operation timed out")
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="The language service timed out. Please try again.",
            ) from exc
        return SummarizeResponse(summary=summary)
    except QueryLimitExceededError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(exc),
        ) from exc
    except (TimeoutError, APITimeoutError) as exc:
        logger.warning("Provider-backed operation timed out")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="The language service timed out. Please try again.",
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
        if not worker_started:
            await release_worker_leases()
