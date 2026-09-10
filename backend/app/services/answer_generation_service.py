"""
Answer Generation Service

Handles document retrieval, reranking, LLM invocation, and response formatting.
Extracted from RAGService as part of service splitting (200-300 lines per service).

Responsibilities:
- Execute retrieval with query expansion
- Rerank documents by relevance
- Generate LLM responses with conversation history
- Format sources and metadata
"""

import re
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, List, Optional, Tuple

from langchain_core.language_models import BaseChatModel

from app.core.config import settings
from app.core.constants import LLMConstants, QueryConstants
from app.core.logging import logger
from app.repositories.vector_store_repository import VectorStoreRepository
from app.schemas.rag_schema import AnswerWithEvidence, ConversationMessage
from app.services.language_service import LanguageService
from app.services.query_expansion_service import QueryExpansionService
from app.services.reranking_service import RerankingService
from app.services.translation_service import TranslationService
SourceCitationData = dict[str, str | int | None]
COMPOUND_QUERY_SPLIT = re.compile(
    r"\s+(?:e|ed)\s+(?=(?:quale|quali|perché|perche|chi|cosa|come)\b)", re.IGNORECASE
)
QUESTION_WORDS = {
    "Qual",
    "Quale",
    "Quali",
    "Che",
    "Chi",
    "Come",
    "Perché",
    "Perche",
    "What",
    "Which",
    "Who",
    "How",
    "Why",
}
PROPER_NOUN_PATTERN = re.compile(r"\b[A-ZÀ-ÖØ-Þ][\w-]*\b")
# ``\w`` includes underscores, so it must not overlap with the separator class.
# Keeping identifier segments and separators disjoint prevents regex backtracking.
IDENTIFIER_PATTERN = re.compile(r"\b[^\W_-]+(?:[_-][^\W_-]+)+\b")
GENERIC_LEXICAL_TERMS = {"InGen"}


def _build_rag_prompt(
    context: str,
    history: str,
    current_user_message: str,
    response_language: str,
) -> str:
    """Build the compact answer-generation payload."""
    sections = [settings.RAG_SYSTEM_PROMPT]
    sections.append(f"LANG:{response_language}")
    sections.append(f"Q:\n{current_user_message}")
    if history:
        sections.append(f"H:\n{history}")
    sections.append(f"C:\n{context}")
    return "\n\n".join(sections)


class AnswerGenerationService:
    """
    Specialized service for answer generation operations.

    Part of RAGService refactoring to maintain 200-300 lines per service.
    Handles the complete RAG pipeline from retrieval to formatted response.
    """

    def __init__(  # pylint: disable=too-many-arguments
        self,
        llm: BaseChatModel,
        repository: VectorStoreRepository,
        language_service: LanguageService,
        translation_service: TranslationService,
        *,  # Force keyword-only arguments below
        query_expansion_service: QueryExpansionService,
        reranking_service: RerankingService,
    ) -> None:
        """
        Initialize AnswerGenerationService with all required dependencies.

        Args:
            llm: Main LLM for answer generation
            repository: Vector store repository for retrieval
            language_service: Language detection service
            translation_service: Translation service
            query_expansion_service: Query expansion service
            reranking_service: Document reranking service
        """
        self.llm = llm
        self.repository = repository
        self.language_service = language_service
        self.translation_service = translation_service
        self.query_expansion_service = query_expansion_service
        self.reranking_service = reranking_service

    def generate_answer(  # pylint: disable=too-many-arguments
        self,
        query: str,
        user_id: str,
        conversation_history: Optional[List[ConversationMessage]] = None,
        output_language: Optional[str] = None,
        *,  # Force keyword-only arguments below
        query_language: Optional[str] = None,
        response_language: Optional[str] = None,
        current_user_message: Optional[str] = None,
        retrieval_queries: Optional[List[str]] = None,
        include_files: Optional[List[str]] = None,
        exclude_files: Optional[List[str]] = None,
    ) -> Tuple[str, List[SourceCitationData]]:
        """
        Generate answer using RAG pipeline: retrieval, reranking, LLM invocation.

        Args:
            query: The user's question (potentially reformulated)
            user_id: User identifier for multi-tenancy
            conversation_history: Optional conversation context
            output_language: Optional target language for response
            include_files: Optional list of filenames to restrict search
            exclude_files: Optional list of filenames to exclude

        Returns:
            Tuple of (formatted_answer, retrieved source citations)
        """
        conversation_history = conversation_history or []
        current_user_message = current_user_message or query

        logger.info(f"🔍 Starting RAG query for user: {user_id}")
        logger.info(f"📝 Query: {query[:100]}{'...' if len(query) > 100 else ''}")

        if include_files:
            logger.info(f"📂 File filter: INCLUDE {include_files}")
        if exclude_files:
            logger.info(f"🚫 File filter: EXCLUDE {exclude_files}")

        query_language_code = (query_language or self.language_service.detect_language(query)).upper()
        response_language = response_language or self.language_service.resolve_response_language(
            current_user_message, output_language=output_language
        )
        logger.info(f"✅ Detected query language: {query_language_code}")

        logger.info(f"🌍 Resolved response language: {response_language}")

        # Translate query for retrieval (English works best)
        if query_language_code != "EN":
            try:
                translated_query = self.translation_service.translate_query_to_language(
                    query, "EN"
                )
                logger.info(f"🔄 Translated for retrieval: {translated_query[:100]}")
            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.error(f"❌ Translation failed: {e}, using original query")
                translated_query = query
        else:
            translated_query = query

        # Retrieve documents with query expansion
        context_docs = self._retrieve_and_rerank(
            translated_query,
            query,
            user_id,
            include_files=include_files,
            exclude_files=exclude_files,
            retrieval_queries=retrieval_queries,
        )

        # Handle no documents found
        if not context_docs:
            return self._generate_llm_response(
                query, current_user_message, [], conversation_history, response_language
            )

        # Generate LLM response
        final_answer, source_documents = self._generate_llm_response(
            query, current_user_message, context_docs, conversation_history, response_language
        )

        logger.info(
            "✅ Answer generated by the response model "
            f"(Sources: {len(source_documents)})"
        )
        return final_answer, source_documents

    def _retrieve_and_rerank(
        self,
        translated_query: str,
        original_query: str,
        user_id: str,
        *,  # Force keyword-only arguments below
        include_files: Optional[List[str]],
        exclude_files: Optional[List[str]],
        retrieval_queries: Optional[List[str]] = None,
    ) -> List[Any]:
        """
        Execute retrieval with query expansion and rerank results.

        Args:
            translated_query: Query translated to English for retrieval
            original_query: Original user query for reranking
            user_id: User identifier
            include_files: Optional file filter (include only)
            exclude_files: Optional file filter (exclude)

        Returns:
            List of reranked documents
        """
        # Generate alternative queries
        expansion_started = time.perf_counter()
        compound_queries = self._validated_compound_queries(retrieval_queries)
        alternative_queries = (
            []
            if compound_queries
            else self.query_expansion_service.generate_alternative_queries(translated_query)
        )
        expansion_ms = (time.perf_counter() - expansion_started) * 1000
        logger.info(f"📝 Generated {len(alternative_queries)} alternative queries")
        logger.info(f"⏱️ RAG timing | query_expansion={expansion_ms:.2f}ms")

        # Keep the first occurrence and preserve ordering: this avoids paying for
        # semantically identical searches while leaving the retrieval pool and
        # reranker inputs unchanged for distinct queries.
        all_queries = []
        seen_queries = set()
        for candidate in [translated_query] + alternative_queries + compound_queries:
            normalized = " ".join(candidate.lower().split())
            if normalized and normalized not in seen_queries:
                seen_queries.add(normalized)
                all_queries.append(candidate)

        # Setup retriever
        retriever = self.repository.get_retriever(
            user_id=user_id,
            k=(
                min(QueryConstants.BASE_RETRIEVAL_K, QueryConstants.FINAL_RETRIEVAL_K * 2)
                if compound_queries
                else QueryConstants.BASE_RETRIEVAL_K
            ),  # Keep compound candidate pools bounded.
            include_files=include_files,
            exclude_files=exclude_files,
        )

        # Each Chroma search embeds its query and performs an independent vector
        # lookup. Execute them concurrently while preserving query order before
        # the existing deduplication/reranking stage.
        logger.info(f"🔎 Parallel retrieval for {len(all_queries)} queries")
        retrieval_started = time.perf_counter()

        def search_query(query: str) -> Tuple[List[Any], float]:
            search_started = time.perf_counter()
            docs = retriever.invoke(query)
            return docs, (time.perf_counter() - search_started) * 1000

        with ThreadPoolExecutor(max_workers=min(4, len(all_queries))) as executor:
            search_results = list(executor.map(search_query, all_queries))

        all_retrieved_docs = []
        doc_ids = set()

        for idx, (docs, search_ms) in enumerate(search_results, 1):
            logger.info(
                f"⏱️ RAG timing | vector_search_{idx}={search_ms:.2f}ms | "
                f"chunks={len(docs)}"
            )

            for doc in docs:
                doc_id = self._document_key(doc)

                if doc_id not in doc_ids:
                    all_retrieved_docs.append(doc)
                    doc_ids.add(doc_id)

        lexical_terms = self._extract_lexical_terms([original_query] + compound_queries)
        if lexical_terms:
            lexical_docs = self.repository.lexical_candidate_search(user_id, lexical_terms)
            logger.info(
                "🔤 Lexical candidate lookup for %s distinctive terms returned %s chunks",
                len(lexical_terms),
                len(lexical_docs),
            )
            for document in lexical_docs:
                document_id = self._document_key(document)
                if document_id not in doc_ids:
                    all_retrieved_docs.append(document)
                    doc_ids.add(document_id)

        unique_files = {
            doc.metadata.get("original_filename", "Unknown")
            for doc in all_retrieved_docs
        }
        logger.info(
            f"📚 Retrieved {len(all_retrieved_docs)} chunks from {len(unique_files)} files"
        )
        logger.info(
            f"⏱️ RAG timing | vector_search_total="
            f"{(time.perf_counter() - retrieval_started) * 1000:.2f}ms"
        )

        if compound_queries:
            all_retrieved_docs = self._rrf_order(all_retrieved_docs, search_results)

        # Rerank to top N
        logger.info(f"🎯 Reranking documents → top {QueryConstants.FINAL_RETRIEVAL_K}")
        reranking_started = time.perf_counter()
        context_docs = self.reranking_service.rerank_documents(
            documents=all_retrieved_docs,
            original_query=original_query,
            alternative_queries=alternative_queries + compound_queries,
            top_n=QueryConstants.FINAL_RETRIEVAL_K,
            required_query_groups=compound_queries,
        )
        logger.info(f"✨ Reranking completed: {len(context_docs)} documents")
        logger.info(
            f"⏱️ RAG timing | reranking="
            f"{(time.perf_counter() - reranking_started) * 1000:.2f}ms"
        )

        return context_docs

    @staticmethod
    def _validated_compound_queries(retrieval_queries: Optional[List[str]]) -> List[str]:
        """Accept only the bounded structured compound-query output."""
        if not retrieval_queries or len(retrieval_queries) > 2:
            return []
        queries = [
            query.strip()
            for query in retrieval_queries
            if isinstance(query, str) and query.strip()
        ]
        return queries if len(queries) == 2 else []

    @staticmethod
    def _split_compound_retrieval_queries(query: str) -> List[str]:
        """Legacy compatibility helper; structured parser output drives production use."""
        parts = [
            part.strip(" ,?.")
            for part in COMPOUND_QUERY_SPLIT.split(query)
            if part.strip()
        ]
        if len(parts) < 2:
            return []
        proper_nouns = [
            token for token in PROPER_NOUN_PATTERN.findall(query) if token not in QUESTION_WORDS
        ]
        anchor = next(
            (token for token in proper_nouns if token.isupper() or "-" in token),
            proper_nouns[0] if proper_nouns else "",
        )
        return [parts[0]] + [f"{anchor} {part}".strip() for part in parts[1:]]

    @staticmethod
    def _rrf_order(
        documents: List[Any], search_results: List[Tuple[List[Any], float]]
    ) -> List[Any]:
        """Order merged compound candidates with reciprocal-rank fusion."""
        scores: dict[int, float] = {}
        for ranked_documents, _search_ms in search_results:
            for rank, document in enumerate(ranked_documents, start=1):
                key = AnswerGenerationService._document_key(document)
                scores[key] = scores.get(key, 0.0) + 1.0 / (60 + rank)
        return sorted(
            documents,
            key=lambda document: scores.get(
                AnswerGenerationService._document_key(document), 0.0
            ),
            reverse=True,
        )

    @staticmethod
    def _document_key(document: Any) -> int:
        """Use the same content/metadata identity for merging and ranking."""
        metadata_tuple = tuple(sorted(document.metadata.items()))
        return hash((document.page_content, metadata_tuple))

    @staticmethod
    def _extract_lexical_terms(queries: List[str]) -> List[str]:
        """Keep a few high-signal IDs or proper names for bounded lexical recall."""
        terms = []
        for query in queries:
            query_terms = PROPER_NOUN_PATTERN.findall(query)
            query_terms.extend(IDENTIFIER_PATTERN.findall(query))
            for term in query_terms:
                if term in QUESTION_WORDS or term in GENERIC_LEXICAL_TERMS:
                    continue
                if term not in terms:
                    terms.append(term)
        identifiers = [term for term in terms if term.isupper() or "-" in term or "_" in term]
        names = [term for term in terms if term not in identifiers]
        return (identifiers + names)[:3]

    def _generate_llm_response(  # pylint: disable=too-many-positional-arguments
        self,
        query: str,
        current_user_message: str,
        context_docs: List[Any],
        conversation_history: List[ConversationMessage],
        response_language: str,
    ) -> Tuple[str, List[SourceCitationData]]:
        """
        Generate LLM response with context and history.

        Args:
            query: Retrieval query
            current_user_message: Raw message from the current user turn
            context_docs: Retrieved and reranked documents
            conversation_history: Conversation messages
            target_language: Target response language code

        Returns:
            Tuple of (formatted_answer, retrieved source citations)
        """
        history_str = self._format_conversation_history(conversation_history)
        context_by_id = {
            f"C{index}": document for index, document in enumerate(context_docs, start=1)
        }
        context_str = self._format_context_documents(context_by_id)
        final_llm_query = self._build_final_prompt(
            context_str, history_str, current_user_message, response_language
        )

        try:
            final_answer, evidence_ids = self._invoke_llm_and_translate(
                final_llm_query
            )
            return final_answer, self._citations_from_evidence_ids(
                context_by_id, evidence_ids
            )

        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error(f"❌ Error during LLM invocation: {e}")
            return self._get_fallback_response(), []

    def _format_conversation_history(
        self, conversation_history: List[ConversationMessage]
    ) -> str:
        """
        Format conversation history for prompt.

        Args:
            conversation_history: List of conversation messages

        Returns:
            Formatted history string
        """
        if not conversation_history:
            return ""

        history_formatted = []
        for msg in conversation_history:
            if msg.role == "user":
                history_formatted.append(f"U|{msg.content}")
            else:
                answer_content = msg.content.split("\n\n📚 Fonti:")[0].strip()
                history_formatted.append(f"A|{answer_content}")

        return "\n".join(history_formatted)

    def _format_context_documents(self, context_by_id: dict[str, Any]) -> str:
        """
        Format retrieved documents as context string.

        Args:
            context_docs: Retrieved and reranked documents

        Returns:
            Formatted context string
        """
        return "\n---\n".join(
            [
                f"[{context_id}|{document.metadata.get('original_filename', 'Unknown')}"
                f"{self._compact_page_label(document.metadata.get('page_number'))}]\n"
                f"{document.page_content.strip()}"
                for context_id, document in context_by_id.items()
            ]
        )

    @staticmethod
    def _compact_page_label(page_number: Any) -> str:
        """Return an optional compact page suffix without changing citation IDs."""
        normalized = AnswerGenerationService._normalize_page_number(page_number)
        return f"|p{normalized}" if normalized is not None else ""

    def _build_final_prompt(
        self, context_str: str, history_str: str, query: str, response_language: str
    ) -> str:
        """
        Build final LLM prompt with context and history.

        Args:
            context_str: Formatted context documents
            history_str: Formatted conversation history
            query: User's query
            target_language: Target response language

        Returns:
            Final prompt string
        """
        rag_prompt = _build_rag_prompt(
            context_str, history_str, query, response_language
        )

        return (
            f"{rag_prompt}\n\n"
            f"--- FINAL INSTRUCTION ---\n"
            "Return a structured response with `answer` and `evidence_ids`. "
            "Answer only from the supplied context. Select only IDs of passages that "
            "materially support the answer; do not select merely related context. "
            "Use the minimum sufficient evidence, normally no more than three IDs, "
            "unless additional IDs support distinct claims. Never invent IDs or source "
            "details. If the context does not support an answer, follow the existing "
            "insufficient-evidence behavior and return an empty evidence_ids list."
        )

    def _invoke_llm_and_translate(
        self, prompt: str, _legacy_target_language: Optional[str] = None
    ) -> Tuple[str, List[str]]:
        """
        Invoke LLM and translate response if needed.

        Args:
            prompt: LLM prompt
            target_language: Target response language

        Returns:
            Final translated answer and context IDs selected as evidence
        """
        logger.info("💬 Invoking LLM for answer generation...")
        structured_llm = self.llm.with_structured_output(AnswerWithEvidence)
        llm_response = structured_llm.invoke(
            prompt, max_tokens=LLMConstants.MAX_TOKENS
        )
        if not isinstance(llm_response, AnswerWithEvidence):
            llm_response = AnswerWithEvidence.model_validate(llm_response)

        final_answer = llm_response.answer.strip()

        return final_answer, llm_response.evidence_ids

    @staticmethod
    def _normalize_page_number(value: Any) -> int | None:
        """Return a valid one-based PDF page number from trusted chunk metadata."""
        if isinstance(value, int) and not isinstance(value, bool) and value > 0:
            return value
        if isinstance(value, str) and value.isdecimal() and int(value) > 0:
            return int(value)
        return None

    def _citations_from_evidence_ids(
        self, context_by_id: dict[str, Any], evidence_ids: List[str]
    ) -> List[SourceCitationData]:
        """Map valid selected context IDs to trusted filename/page metadata."""
        citations: List[SourceCitationData] = []
        seen: set[tuple[str, int | None]] = set()
        selected_ids = {
            evidence_id
            for evidence_id in evidence_ids
            if isinstance(evidence_id, str) and evidence_id in context_by_id
        }

        # Preserve reranking order for the subset chosen by the model.
        for context_id, document in context_by_id.items():
            if context_id not in selected_ids:
                continue
            filename = document.metadata.get("original_filename")
            if not isinstance(filename, str) or not filename:
                continue
            page_number = self._normalize_page_number(document.metadata.get("page_number"))
            citation_key = (filename, page_number)
            if citation_key in seen:
                continue
            seen.add(citation_key)
            citations.append({"filename": filename, "page_number": page_number})

        return citations

    def _append_sources_to_answer(
        self, answer: str, source_documents: List[str], target_language: str
    ) -> str:
        """
        Append source citations to answer.

        Args:
            answer: Generated answer
            source_documents: List of source filenames
            target_language: Target language for sources label

        Returns:
            Answer with appended sources
        """
        if not source_documents:
            return answer

        sources_label = self._get_sources_label(target_language)
        sources_list = "\n".join([f"- {doc}" for doc in source_documents])
        return f"{answer}\n\n📚 {sources_label}:\n{sources_list}"

    def _get_fallback_response(self) -> str:
        """
        Generate fallback response on error.

        Args:
            target_language: Resolved response language

        Returns:
            Translated error message
        """
        return "An unexpected error occurred during answer generation."

    def _handle_no_documents(
        self, query_language: str
    ) -> Tuple[str, List[SourceCitationData]]:
        """
        Handle case when no documents are retrieved.

        Args:
            query_language: Original query language code

        Returns:
            Tuple of (fallback_message, empty_source_list)
        """
        logger.warning("⚠️ No relevant documents found")
        fallback_answer = (
            "I cannot answer this question based on the documents provided."
        )
        translated_fallback = self.language_service.translate_answer_back(
            fallback_answer, query_language
        )
        logger.info(f"✅ Fallback answer translated to {query_language}")
        return translated_fallback, []

    def _get_sources_label(self, language_code: str) -> str:
        """
        Get translated 'Sources' label.

        Args:
            language_code: ISO language code (IT, EN, FR, etc.)

        Returns:
            Translated label for 'Sources'
        """
        sources_translations = {
            "IT": "Fonti",
            "EN": "Sources",
            "FR": "Sources",
            "DE": "Quellen",
            "ES": "Fuentes",
            "PT": "Fontes",
        }
        return sources_translations.get(language_code, "Sources")
