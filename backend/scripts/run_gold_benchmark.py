"""Run the frozen 13-question RAG evaluation inside the Railway backend runtime.

This is intentionally a one-off command, not an HTTP endpoint. It uses the
mounted production Chroma volume and normal query usage reservation, but never
creates Firestore conversation documents.
"""

import argparse
import json
import time
from dataclasses import asdict, dataclass
from typing import Any, Callable

from langchain_community.callbacks.manager import get_openai_callback

from app.db.chroma_client import get_chroma_collection_direct, get_vector_store
from app.repositories.vector_store_repository import VectorStoreRepository
from app.routers.query_router import _get_user_tier_limits, _reserve_and_enforce_query_limit
from app.services.query_parser_service import query_parser_service
from app.services.rag_orchestrator_service import RAGService
from app.services.usage_tracking_service import get_usage_service


GOLD_QUESTIONS = [
    "Quale veicolo T-CAR ha superato il test di override manuale e quali invece lo hanno fallito?",
    "Che cosa fa esattamente il comando SRI_LOCKOUT_F1?",
    "Chi è autorizzato ad accedere al magazzino di riserva del Cloruro di Potassio e degli integratori L-LIMIT?",
    "Qual è il consumo giornaliero del Brachiosauro e quale caratteristica genetica unica presenta?",
    (
        "Perché InGen chiama il ceppo VELO “Velociraptor” anche se è più vicino "
        "al Deinonychus, e perché questo animale rappresenta un rischio operativo "
        "eccezionale?"
    ),
    "Qual è il rischio di inversione sessuale del ceppo VELO e quali documenti lo confermano?",
    "Perché il sistema V4.1 costituiva un single point of failure per i veicoli del tour durante un blackout?",
    "Perché il protocollo L-LIMIT non poteva essere considerato un meccanismo di contenimento sufficiente?",
    (
        "Quali prove mostrano che il rischio rappresentato dai VELO era conosciuto "
        "prima del fallimento del contenimento ma non fu gestito adeguatamente?"
    ),
    (
        "Come differiscono il Gruppo Tattico e il Gruppo di Dominanza dei VELO-B "
        "e quali conseguenze hanno avuto i loro scontri territoriali?"
    ),
    "Qual è il codice numerico esatto a 4 cifre per sbloccare manualmente i T-CAR?",
    "Qual è il dosaggio numerico esatto del protocollo L-LIMIT Max-Dosage?",
    "Tutti e quattro i T-CAR hanno fallito il test di override manuale?",
]


@dataclass
class QueryMetrics:
    """Metrics captured without changing the public RAG API."""

    candidates: int = 0
    final_evidence: int = 0
    reranking_ms: float = 0.0


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--user-id", required=True, help="Existing production corpus owner UID"
    )
    parser.add_argument(
        "--confirm-production",
        action="store_true",
        help="Required acknowledgement that this makes 13 production LLM calls.",
    )
    return parser.parse_args()


def _instrument_reranker(
    rag_service: RAGService, metrics: QueryMetrics
) -> Callable[..., list[Any]]:
    """Wrap only this one-off service instance to collect retrieval diagnostics."""
    reranker = rag_service.answer_generation_service.reranking_service
    original_rerank = reranker.rerank_documents

    def measured_rerank(*args: Any, **kwargs: Any) -> list[Any]:
        metrics.candidates = len(kwargs.get("documents", args[0] if args else []))
        started = time.perf_counter()
        selected = original_rerank(*args, **kwargs)
        metrics.reranking_ms = round((time.perf_counter() - started) * 1000, 2)
        metrics.final_evidence = len(selected)
        return selected

    reranker.rerank_documents = measured_rerank  # type: ignore[method-assign]
    return original_rerank


def _reserve_query(user_id: str) -> None:
    """Use the same usage reservation policy as the production query router."""
    tier, max_queries = _get_user_tier_limits(user_id)
    _reserve_and_enforce_query_limit(get_usage_service(), user_id, tier, max_queries)


def _run_question(rag_service: RAGService, user_id: str, question: str) -> dict[str, Any]:
    """Run one isolated query with no persisted or conversational history."""
    metrics = QueryMetrics()
    reranker = rag_service.answer_generation_service.reranking_service
    original_rerank = _instrument_reranker(rag_service, metrics)
    available_documents = rag_service.get_user_documents(user_id)
    file_filter = query_parser_service.extract_file_filters(
        query=question,
        available_files=[document.filename for document in available_documents],
    )
    _reserve_query(user_id)
    started = time.perf_counter()
    try:
        with get_openai_callback() as callback:
            answer, citations = rag_service.answer_query(
                query=file_filter.cleaned_query,
                user_id=user_id,
                conversation_history=[],
                output_language="IT",
                include_files=file_filter.include_files or None,
                exclude_files=file_filter.exclude_files or None,
            )
    finally:
        reranker.rerank_documents = original_rerank  # type: ignore[method-assign]
    return {
        "question": question,
        "answer": answer,
        "citations": citations,
        "metrics": asdict(metrics),
        "total_ms": round((time.perf_counter() - started) * 1000, 2),
        "tokens": {
            "input": callback.prompt_tokens,
            "output": callback.completion_tokens,
            "total": callback.total_tokens,
        },
        "llm_calls": callback.successful_requests,
    }


def main() -> None:
    """Run each frozen question with a fresh history and print JSON only."""
    args = _parse_args()
    if not args.confirm_production:
        raise SystemExit("Refusing production benchmark without --confirm-production")

    repository = VectorStoreRepository(
        vector_store=next(get_vector_store()),
        collection=next(get_chroma_collection_direct()),
    )
    rag_service = RAGService(repository=repository)
    results = [
        _run_question(rag_service, args.user_id, question)
        for question in GOLD_QUESTIONS
    ]
    print(json.dumps({"results": results}, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
