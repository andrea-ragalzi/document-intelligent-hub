"""
RAG Service Module - Main Orchestrator (Refactored)

Thin orchestration layer that delegates to specialized services.
Refactored from 1020-line monolith to ~200-line orchestrator.

Architecture:
- DocumentIndexingService: PDF processing, chunking, embedding
- QueryProcessingService: Query classification and reformulation
- AnswerGenerationService: Retrieval, reranking, LLM invocation
- DocumentManagementService: CRUD operations for documents
- ConversationService: Conversation summarization
"""

from decimal import Decimal
import time
from typing import Any

from langchain_core.language_models import BaseChatModel

from app.core.logging import logger
from app.ports.uploaded_file import UploadedFilePort
from app.ports.translation import TranslationPort
from app.ports.vector_store import VectorStorePort
from app.schemas.rag_schema import ConversationMessage, DocumentInfo
from app.services.answer_generation_service import AnswerGenerationService
from app.services.conversation_service import ConversationService
from app.services.deterministic_compute_service import DeterministicComputeService
from app.services.deterministic_evidence_service import DeterministicEvidenceService
from app.services.document_classifier_service import document_classifier_service

# Import specialized services
from app.services.document_indexing_service import DocumentIndexingService
from app.services.document_management_service import DocumentManagementService

# Existing services (used by specialized services)
from app.services.language_service import LanguageService
from app.services.query_expansion_service import QueryExpansionService
from app.services.query_processing_service import QueryProcessingService
from app.services.query_routing_service import (
    ComputeOperation,
    DeterministicQueryRouter,
    QueryRoute,
)
from app.services.reranking_service import reranking_service


class RAGService:
    """
    Main RAG Service - Orchestrator

    Thin coordination layer that delegates to specialized services.
    Maintains backward compatibility with existing API.

    Refactored from 1020 lines to ~200 lines by extracting:
    - DocumentIndexingService (340 lines)
    - QueryProcessingService (181 lines)
    - AnswerGenerationService (332 lines)
    - DocumentManagementService (167 lines)
    - ConversationService (82 lines)
    """

    def __init__(
        self,
        repository: VectorStorePort,
        llm: BaseChatModel,
        query_gen_llm: BaseChatModel,
        translation_service: TranslationPort,
        query_expansion_service: QueryExpansionService,
    ) -> None:
        """
        Initialize RAG service with repository and specialized services.

        Args:
            repository: Vector store repository for data access
            llm: Model used for answer generation and reformulation
            query_gen_llm: Model used for classification and summarization
        """
        self.repository = repository

        self.llm = llm
        self.query_gen_llm = query_gen_llm

        # Initialize shared services
        self.language_service = LanguageService()

        # Initialize specialized services with dependencies
        self.indexing_service = DocumentIndexingService(
            repository=repository,
            language_service=self.language_service,
            classifier_service=document_classifier_service,
        )

        self.query_processing_service = QueryProcessingService(
            llm=self.llm, query_gen_llm=self.query_gen_llm
        )
        self.query_router = DeterministicQueryRouter()
        self.deterministic_evidence_service = DeterministicEvidenceService(repository)
        self.deterministic_compute_service = DeterministicComputeService()

        self.answer_generation_service = AnswerGenerationService(
            llm=self.llm,
            repository=repository,
            language_service=self.language_service,
            translation_service=translation_service,
            query_expansion_service=query_expansion_service,
            reranking_service=reranking_service,
        )

        self.document_management_service = DocumentManagementService(
            repository=repository
        )

        self.conversation_service = ConversationService(
            query_gen_llm=self.query_gen_llm
        )

        logger.debug("RAGService initialized with specialized services")

    # === DOCUMENT INDEXING OPERATIONS ===

    async def index_document(
        self,
        file: UploadedFilePort,
        user_id: str,
        document_language: str | None = None,
        document_metadata: dict[str, Any] | None = None,
        allow_unlimited_document: bool = False,
    ) -> tuple[int, str]:
        """
        Delegate to DocumentIndexingService.

        Args:
            file: Uploaded PDF file
            user_id: User identifier
            document_language: Optional language code
            document_metadata: Internal metadata applied to indexed chunks.

        Returns:
            Tuple of (chunks_indexed, detected_language)
        """
        return await self.indexing_service.index_document(
            file, user_id, document_language, document_metadata, allow_unlimited_document
        )

    async def detect_document_language_preview(
        self, file: UploadedFilePort
    ) -> tuple[str, float]:
        """
        Delegate to DocumentIndexingService.

        Args:
            file: Uploaded PDF file

        Returns:
            Tuple of (language_code, confidence)
        """
        return await self.indexing_service.detect_document_language_preview(file)

    # === QUERY PROCESSING & ANSWER GENERATION ===

    def answer_query(
        self,
        query: str,
        user_id: str,
        conversation_history: list[ConversationMessage] | None = None,
        output_language: str | None = None,
        include_files: list[str] | None = None,
        exclude_files: list[str] | None = None,
        raw_user_query: str | None = None,
        retrieval_queries: list[str] | None = None,
    ) -> tuple[str, list[dict[str, str | int | None]]]:
        """
        Process query and generate answer using RAG pipeline.

        Workflow: reformulate contextual queries, then generate a RAG answer.

        Args:
            query: User's question
            user_id: User identifier
            conversation_history: Optional conversation context
            output_language: Optional target language
            include_files: Optional file filter (include only)
            exclude_files: Optional file filter (exclude)

        Returns:
            Tuple of (answer, retrieved source citations)
        """
        conversation_history = conversation_history or []
        current_user_query = raw_user_query or query

        response_language = self.language_service.resolve_response_language(
            current_user_query,
            output_language=output_language,
            recent_user_messages=(
                message.content
                for message in reversed(conversation_history)
                if message.role == "user"
            ),
        )
        use_history = self.query_processing_service.requires_conversation_context(
            query, conversation_history
        )
        relevant_history = conversation_history if use_history else []

        # Step 1: Reformulate query if needed (handles conversational context)
        reformulated_query = self.query_processing_service.reformulate_query(
            query, relevant_history
        )
        retrieval_language = self.language_service.detect_language(reformulated_query)

        # Generate answer with the unchanged full RAG pipeline. The former
        # semantic classification call had no behavioral consumer and was removed.
        answer_args: dict[str, Any] = dict(
            query=reformulated_query,
            user_id=user_id,
            conversation_history=relevant_history,
            query_language=retrieval_language,
            response_language=response_language,
            current_user_message=current_user_query,
            include_files=include_files,
            exclude_files=exclude_files,
        )
        if retrieval_queries:
            return self.answer_generation_service.generate_answer(
                **answer_args, retrieval_queries=retrieval_queries
            )
        return self.answer_generation_service.generate_answer(**answer_args)

    def try_deterministic_query(
        self,
        query: str,
        user_id: str,
        documents: list[DocumentInfo],
        conversation_history: list[ConversationMessage],
    ) -> tuple[str, list[dict[str, str | int | None]], str, str] | None:
        """Return one fully grounded deterministic result, or ``None`` for RAG.

        This is intentionally a single decision and a single route. A failed
        validation is indistinguishable from an unsupported request to callers:
        both continue through normal RAG.
        """
        decision = self.query_router.decide(query, documents, conversation_history)
        if decision.route is QueryRoute.RAG:
            logger.info("Query route | route=rag reason={} luna_invoked=true", decision.reason)
            return None

        started = time.perf_counter()
        try:
            if decision.route is QueryRoute.DIRECT_LOOKUP and decision.term:
                direct_evidence = self.deterministic_evidence_service.occurrences(
                    user_id, decision.term
                )
                if not direct_evidence:
                    return None
                citations = self._unique_citations(direct_evidence)
                if decision.reason == "explicit_page_occurrence_lookup":
                    locations = ", ".join(
                        f"{item['filename']} p.{item['page_number']}"
                        for item in citations
                    )
                    answer = f'"{decision.term}" was found on: {locations}.'
                else:
                    filenames = ", ".join(
                        dict.fromkeys(
                            str(item["filename"])
                            for item in citations
                            if item["filename"] is not None
                        )
                    )
                    answer = f'"{decision.term}" appears in: {filenames}.'
                return answer, citations, decision.route.value, decision.reason

            if decision.route is QueryRoute.DIRECT_EXTRACT and decision.filename and decision.field_label:
                labeled_evidence = self.deterministic_evidence_service.labeled_value(
                    user_id, decision.filename, decision.field_label
                )
                if labeled_evidence is None:
                    return None
                answer = f"{decision.field_label}: {labeled_evidence.value}"
                return (
                    answer,
                    [labeled_evidence.citation()],
                    decision.route.value,
                    decision.reason,
                )

            if decision.route is QueryRoute.COMPUTE and decision.operation is ComputeOperation.COUNT and decision.term:
                evidence = self.deterministic_evidence_service.occurrences(user_id, decision.term)
                by_document = list({item.filename: item for item in evidence}.values())
                if not by_document:
                    return None
                result = self.deterministic_compute_service.compute(
                    ComputeOperation.COUNT,
                    [Decimal("1")] * len(by_document),
                    by_document,
                )
                answer = f'{result.value} document(s) mention "{decision.term}".'
                return answer, self._unique_citations(result.evidence), decision.route.value, decision.reason
        except (TypeError, ValueError):
            logger.info("Query route validation failed | route={} luna_invoked=true", decision.route.value)
            return None
        finally:
            elapsed = (time.perf_counter() - started) * 1000
            logger.info(
                "Query route evaluated | route={} reason={} duration_ms={:.2f} luna_invoked={}",
                decision.route.value,
                decision.reason,
                elapsed,
                "false",
            )
        return None

    @staticmethod
    def _unique_citations(evidence: list[Any]) -> list[dict[str, str | int | None]]:
        citations: list[dict[str, str | int | None]] = []
        seen: set[tuple[str, int | None]] = set()
        for item in evidence:
            citation = item.citation()
            key = (str(citation["filename"]), citation["page_number"] if isinstance(citation["page_number"], int) else None)
            if key not in seen:
                seen.add(key)
                citations.append(citation)
        return citations[:5]

    # === DOCUMENT MANAGEMENT OPERATIONS ===

    def get_user_documents(self, user_id: str) -> list[Any]:
        """
        Delegate to DocumentManagementService.

        Args:
            user_id: User identifier
            include_demo: Whether to include the bundled starter document.

        Returns:
            List of DocumentInfo objects
        """
        return self.document_management_service.get_user_documents(user_id)

    def delete_user_document(self, user_id: str, filename: str) -> int:
        """
        Delegate to DocumentManagementService.

        Args:
            user_id: User identifier
            filename: Document filename to delete

        Returns:
            Number of chunks deleted
        """
        return self.document_management_service.delete_user_document(user_id, filename)

    def delete_all_user_documents(self, user_id: str) -> int:
        """
        Delegate to DocumentManagementService.

        Args:
            user_id: User identifier

        Returns:
            Number of chunks deleted
        """
        return self.document_management_service.delete_all_user_documents(user_id)

    def get_user_document_count(self, user_id: str, include_demo: bool = True) -> int:
        """
        Delegate to DocumentManagementService.

        Args:
            user_id: User identifier

        Returns:
            Number of unique documents
        """
        return self.document_management_service.get_user_document_count(
            user_id, include_demo=include_demo
        )

    def user_document_exists(self, user_id: str, filename: str) -> bool:
        """Return whether this authenticated user's document is already indexed."""
        return self.repository.check_document_exists(user_id, filename)

    # === CONVERSATION OPERATIONS ===

    def generate_conversation_summary(
        self, conversation_history: list[ConversationMessage]
    ) -> str:
        """
        Delegate to ConversationService.

        Args:
            conversation_history: List of conversation messages

        Returns:
            Concise summary string
        """
        return self.conversation_service.generate_conversation_summary(
            conversation_history
        )
