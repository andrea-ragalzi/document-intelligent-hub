"""
Answer Generation Service

Handles document retrieval, reranking, LLM invocation, and response formatting.
Extracted from RAGService as part of service splitting (200-300 lines per service).

Responsibilities:
- Execute retrieval with query expansion
- Rerank documents by relevance
- Generate LLM responses with conversation history
- Translate responses to target language
- Format sources and metadata
"""

from typing import Any, List, Optional, Tuple

from app.core.config import settings
from app.core.constants import QueryConstants
from app.core.logging import logger
from app.repositories.vector_store_repository import VectorStoreRepository
from app.schemas.rag_schema import ConversationMessage
from app.services.language_service import LanguageService
from app.services.query_expansion_service import QueryExpansionService
from app.services.reranking_service import RerankingService
from app.services.translation_service import TranslationService
from langchain_core.language_models import BaseChatModel


def _build_rag_prompt(context: str, question: str) -> str:
    """Build RAG prompt without conversation history."""
    return (
        f"{settings.RAG_SYSTEM_PROMPT}\n\n"
        f"Context: {context}\n\n"
        f"Question: {question}"
    )


def _build_rag_prompt_with_history(context: str, history: str, question: str) -> str:
    """Build RAG prompt with conversation history."""
    return (
        f"{settings.RAG_SYSTEM_PROMPT}\n\n"
        f"Conversation History:\n{history}\n\n"
        f"Context: {context}\n\n"
        f"New Question: {question}"
    )


class AnswerGenerationService:
    """
    Specialized service for answer generation operations.

    Part of RAGService refactoring to maintain 200-300 lines per service.
    Handles the complete RAG pipeline from retrieval to formatted response.
    """

    def __init__(
        self,
        llm: BaseChatModel,
        repository: VectorStoreRepository,
        language_service: LanguageService,
        translation_service: TranslationService,
        *,  # Force keyword-only arguments below
        query_expansion_service: QueryExpansionService,
        reranking_service: RerankingService
    ):
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

    def generate_answer(
        self,
        query: str,
        user_id: str,
        conversation_history: Optional[List[ConversationMessage]] = None,
        output_language: Optional[str] = None,
        *,  # Force keyword-only arguments below
        include_files: Optional[List[str]] = None,
        exclude_files: Optional[List[str]] = None
    ) -> Tuple[str, List[str]]:
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
            Tuple of (formatted_answer_with_sources, list_of_source_filenames)
        """
        conversation_history = conversation_history or []

        logger.info(f"🔍 Starting RAG query for user: {user_id}")
        logger.info(f"📝 Query: {query[:100]}{'...' if len(query) > 100 else ''}")

        if include_files:
            logger.info(f"📂 File filter: INCLUDE {include_files}")
        if exclude_files:
            logger.info(f"🚫 File filter: EXCLUDE {exclude_files}")

        # Detect languages
        query_language_code = self.language_service.detect_language(query).upper()
        target_response_language = (
            output_language.upper() if output_language else query_language_code
        )

        logger.info(f"🌍 Query Language: {query_language_code} → Target: {target_response_language}")

        # Translate query for retrieval (English works best)
        if query_language_code != "EN":
            translated_query = self.translation_service.translate_query_to_language(query, "EN")
            logger.info(f"🔄 Translated for retrieval: {translated_query[:100]}")
        else:
            translated_query = query

        # Retrieve documents with query expansion
        context_docs = self._retrieve_and_rerank(
            translated_query,
            query,
            user_id,
            include_files=include_files,
            exclude_files=exclude_files
        )

        # Handle no documents found
        if not context_docs:
            return self._handle_no_documents(query_language_code)

        # Generate LLM response
        final_answer, source_documents = self._generate_llm_response(
            query, context_docs, conversation_history, target_response_language
        )

        logger.info(
            f"✅ Answer generated in {target_response_language} "
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
        exclude_files: Optional[List[str]]
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
        alternative_queries = self.query_expansion_service.generate_alternative_queries(
            translated_query
        )
        logger.info(f"📝 Generated {len(alternative_queries)} alternative queries")

        all_queries = [translated_query] + alternative_queries

        # Setup retriever
        retriever = self.repository.get_retriever(
            user_id=user_id,
            k=QueryConstants.BASE_RETRIEVAL_K,  # Large pool for comprehensive search
            include_files=include_files,
            exclude_files=exclude_files
        )

        # Parallel retrieval
        logger.info(f"🔎 Parallel retrieval for {len(all_queries)} queries")
        all_retrieved_docs = []
        doc_ids = set()

        for idx, q in enumerate(all_queries, 1):
            docs = retriever.invoke(q)
            logger.info(f"🔎 Query {idx}/{len(all_queries)}: Found {len(docs)} chunks")

            for doc in docs:
                metadata_tuple = tuple(sorted(doc.metadata.items()))
                doc_id = hash((doc.page_content, metadata_tuple))

                if doc_id not in doc_ids:
                    all_retrieved_docs.append(doc)
                    doc_ids.add(doc_id)

        unique_files = {
            doc.metadata.get("original_filename", "Unknown") for doc in all_retrieved_docs
        }
        logger.info(f"📚 Retrieved {len(all_retrieved_docs)} chunks from {len(unique_files)} files")

        # Rerank to top N
        logger.info(f"🎯 Reranking documents → top {QueryConstants.FINAL_RETRIEVAL_K}")
        context_docs = self.reranking_service.rerank_documents(
            documents=all_retrieved_docs,
            original_query=original_query,
            alternative_queries=alternative_queries,
            top_n=QueryConstants.FINAL_RETRIEVAL_K
        )
        logger.info(f"✨ Reranking completed: {len(context_docs)} documents")

        return context_docs

    def _generate_llm_response(
        self,
        query: str,
        context_docs: List[Any],
        conversation_history: List[ConversationMessage],
        target_language: str
    ) -> Tuple[str, List[str]]:
        """
        Generate LLM response with context and history.

        Args:
            query: User's question
            context_docs: Retrieved and reranked documents
            conversation_history: Conversation messages
            target_language: Target response language code

        Returns:
            Tuple of (formatted_answer, source_files)
        """
        # Format conversation history
        history_formatted = []
        for msg in conversation_history:
            if msg.role == "user":
                history_formatted.append(f"User: {msg.content}")
            else:
                # Extract answer without sources
                answer_content = msg.content.split("\n\n📚 Fonti:")[0].strip()
                history_formatted.append(f"Assistant: {answer_content}")

        history_str = "\n".join(history_formatted) if history_formatted else "No history available."

        # Format context
        context_str = "\n---\n".join([
            f"Section: {doc.metadata.get('chapter_title', 'Document Start')}\n"
            f"Source: {doc.metadata.get('original_filename', 'Unknown')}\n"
            f"Content:\n{doc.page_content.strip()}"
            for doc in context_docs
        ])

        # Build prompt (with or without history)
        if history_str and history_str != "No history available.":
            rag_prompt = _build_rag_prompt_with_history(context_str, history_str, query)
        else:
            rag_prompt = _build_rag_prompt(context_str, query)

        # Add language instruction
        final_llm_query = (
            f"{rag_prompt}\n\n"
            f"--- FINAL INSTRUCTION ---\n"
            f"You MUST respond ENTIRELY in the target language: {target_language}. "
            f"Do not include source citations; they will be handled separately."
        )

        try:
            # LLM invocation
            logger.info("💬 Invoking LLM for answer generation...")
            llm_response = self.llm.invoke(final_llm_query).content
            final_answer = str(llm_response).strip()

            # Extract source files
            source_documents = sorted({
                doc.metadata.get("original_filename", "Unknown") for doc in context_docs
            })

            # Translate if needed
            detected_lang = self.language_service.detect_language(final_answer).upper()
            if target_language != "EN" and detected_lang == "EN":
                final_answer = self.translation_service.translate_answer_back(
                    final_answer, target_language
                )
                logger.debug(f"🔄 Answer translated to {target_language}")

            # Append sources
            if source_documents:
                sources_label = self._get_sources_label(target_language)
                sources_list = "\n".join([f"- {doc}" for doc in source_documents])
                final_answer = f"{final_answer}\n\n📚 {sources_label}:\n{sources_list}"

            return final_answer, source_documents

        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error(f"❌ Error during LLM invocation: {e}")
            query_lang = self.language_service.detect_language(query).upper()
            fallback = self.language_service.translate_answer_back(
                "An unexpected error occurred during answer generation.", query_lang
            )
            return fallback, []

    def _handle_no_documents(self, query_language: str) -> Tuple[str, List[str]]:
        """
        Handle case when no documents are retrieved.

        Args:
            query_language: Original query language code

        Returns:
            Tuple of (fallback_message, empty_source_list)
        """
        logger.warning("⚠️ No relevant documents found")
        fallback_answer = "I cannot answer this question based on the documents provided."
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
            "PT": "Fontes"
        }
        return sources_translations.get(language_code, "Sources")
